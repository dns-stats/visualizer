#!/usr/bin/env python3
#
# Copyright 2019-2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Check the used space percentage on the Visualizer ClickHouse data partition.
# If the percentage is over a threshold, find the oldest partition and
# possibly delete it. 'clickhouse-client' must be installed.
#
# Usage: dsv-prune  [-t|--threshold <percentage>] [--force] [--report-only]
#

import datetime
import logging
import sys
import time

import clickhouse_driver
import clickhouse_driver.errors

description = 'check ClickHouse used space and delete partitions on low space.'

class PruneError(Exception):
    pass

def user_table_name(table):
    return table[7:] if table.startswith('.inner.') else table

def query_all_servers(servers, query, params=None):
    return [(server[0], server[1].execute(query, params)) for server in servers.items()]

def get_partitions(servers, dataset_info, max_age=None):
    sql_fmt = "SELECT database,table,partition FROM system.parts " \
        "WHERE database=%(database)s " \
        "AND active AND match(table, %(table)s) " \
        "{age_clause} GROUP BY database,table,partition"
    sql = sql_fmt.format(age_clause='AND max_date < %(before_date)s' if max_age else '')
    before_date = datetime.date.today() - datetime.timedelta(days=max_age) if max_age else None
    recs = query_all_servers(servers, sql,
                             {'database': dataset_info['database'],
                              'table': dataset_info['table_pattern'],
                              'before_date': before_date})
    for extra in dataset_info['extra_tables']:
        ex = extra.split('.', 1)
        if len(ex) > 1:
            ex_db = ex[0].strip()
            ex_table = ex[1].strip()
        else:
            ex_db = dataset_info['database']
            ex_table = ex[0].strip()
        recs.extend(query_all_servers(servers, sql,
                                      {'database': ex_db,
                                       'table': ex_table,
                                       'before_date': before_date}))

    # We now have a list: [server name, (database, table, partition)]. Turn
    # this into a dict of {partition: {(database, table): [server names]}},
    # with the partitions and for each partition a dict of (database, table)
    # holding a list of each server on which that table/partition is found.
    res = {}
    for rec in recs:
        server = rec[0]
        for part_rec in rec[1]:
            table = (part_rec[0], user_table_name(part_rec[1]))
            part = part_rec[2]
            if part in res:
                if table in res[part]:
                    res[part][table].append(server)
                else:
                    res[part][table] = [ server ]
            else:
                res[part] = { table: [ server ] }
    return res

def ask_delete(partition, db_table, force):
    print('Delete partition {partition} in database {database} table {table}.'.format(
        partition=partition, database=db_table[0], table=db_table[1]))
    if force:
        logging.info('Partition {partition} in database {database} table {table}: Deletion forced.'.format(
            partition=partition, database=db_table[0], table=db_table[1]))
        return True
    else:
        response = input('Enter DELETEIT to delete this partition -> ')
        if response == 'DELETEIT':
            logging.info('Partition {partition} in database {database} table {table}: '
                         'User commanded partition deletion.'.format(
                             partition=partition, database=db_table[0], table=db_table[1]))
            return True
    return False

def delete_partition(servers, server, db_table, partition, dryrun):
    if dryrun:
        print('Partition {partition} in database {database} table {table} on {server} will be deleted.'.format(
            partition=partition, database=db_table[0],
            table=db_table[1], server=server))
    else:
        sql = "ALTER TABLE {}.{} DROP PARTITION {}".format(db_table[0], db_table[1], partition)
        servers[server].execute(sql)
        print('Partition {partition} in database {database} table {table} deleted.'.format(
            partition=partition, database=db_table[0], table=db_table[1]))
        logging.info('Partition {partition} database {database} table {table} deleted.'.format(
            partition=partition, database=db_table[0], table=db_table[1]))

def age_partitions(servers, partitions, force, dryrun):
    for part in sorted(partitions.keys()):
        for db_table in sorted(partitions[part].keys()):
            if ask_delete(part, db_table, force):
                for server in partitions[part][db_table]:
                    delete_partition(servers, server, db_table, part, dryrun)

def list_partitions(ds_name, partitions):
    print('{} partitions:'.format(ds_name))
    # Output partition info in the format:
    # <database>:
    #   <table>: <partition>, <partition>
    dbs = {}
    for part in sorted(partitions.keys()):
        for t in partitions[part].keys():
            db = t[0]
            table = t[1]
            if db in dbs:
                if table in dbs[db]:
                    dbs[db][table].append(part)
                else:
                    dbs[db][table] = [ part ]
            else:
                dbs[db] = { table: [ part ] }
    for db in sorted(dbs.keys()):
        print('  {db}:'.format(db=db))
        for t in sorted(dbs[db].keys()):
            print('    {table}: {parts}'.format(table=t, parts=','.join(sorted(dbs[db][t]))))

def read_dataset_info(dataset, chcfg):
    try:
        dataset_info = {}
        dataset_info['name'] = chcfg['dataset-name-' + dataset]
        dataset_info['database'] = chcfg['dataset-database-' + dataset]
        dataset_info['table_pattern'] = chcfg['dataset-table-pattern-' + dataset]
        extras = 'dataset-extra-tables-' + dataset
        if extras in chcfg:
            dataset_info['extra_tables'] = [t.strip() for t in chcfg[extras].split(',')]
        else:
            dataset_info['extra_tables'] = []

        remove_max = 'dataset-remove-max-' + dataset
        return dataset_info
    except KeyError as e:
        raise PruneError('Missing configuration information: ' + e)

def disc_threshold_exceeded(servers, threshold):
    print('Checking cluster disc usage...', end='', flush=True)

    # Ensure sysinfo dictionary cache time is expired so we get an
    # up to date reading.
    time.sleep(2)

    usage = query_all_servers(servers,
                              "SELECT dictGetString('sysinfo', 'value', "
                              "tuple('disc-percent-used'))")

    disc = {}
    for s in usage:
        disc[s[0]] = int(s[1][0][0])

    report = 'Visualizer cluster disc usage: '
    res = False
    sep = ''
    for s in sorted(disc.keys()):
        threshold_marker = ''
        if disc[s] >= threshold:
            threshold_marker = '*'
            res = True
        report = report + '{}{}: {}%{}'.format(sep, s, disc[s], threshold_marker)
        sep = ', '

    print('\n{}'.format(report))
    logging.info(report)
    return res

def add_args(parser):
    # Other arguments, new argument style.
    group = parser.add_argument_group('By category', 'Prune data categories by age.')
    group.add_argument('-d', '--age-data',
                       dest='age_data', action='store', default='raw',
                       choices=['5min', 'raw'],
                       help='data to age: 5min or raw',
                       metavar='AGE_DATA')
    group.add_argument('-a', '--max-age',
                       dest='max_age', action='store',
                       type=int, default=365,
                       help='maximum data partition age in days, default %(default)s',
                       metavar='MAX_AGE')
    group.add_argument('-i', '--incremental',
                        dest='incremental', action='store_true', default=False,
                        help='recheck disc usage and stop immediately when below threshold')

    # Remaining global arguments.
    parser.add_argument('-t', '--threshold',
                        dest='threshold', action='store',
                        type=int, default=80,
                        help='set disc usage percentage threshold, default %(default)s',
                        metavar='THRESHOLD')
    parser.add_argument('-l', '--list-partitions',
                        dest='list', action='store_true', default=False,
                        help='just list current raw and aggregated data partitions')
    parser.add_argument('--force',
                        dest='force', action='store_true', default=False,
                        help='don\'t ask, delete the oldest raw data partition')
    parser.add_argument('-n', '--dry-run',
                        dest='dryrun', action='store_true', default=False,
                        help='report partitions to be deleted only')
    parser.add_argument('--report-only',
                        dest='report_only', action='store_true', default=False,
                        help='only report space usage')

def main(args, cfg):
    try:
        clickhouse = cfg['clickhouse']
        ckuser = clickhouse['user']
        ckpass = clickhouse['password']
        servers = {server.strip():
                   clickhouse_driver.Client(host=server.strip(),
                                            user=ckuser,
                                            password=ckpass)
                   for server in clickhouse['servers'].split(',')}

        if args.list:
            for ds in ['raw', '5min']:
                ds_info = read_dataset_info(ds, clickhouse)
                list_partitions(ds_info['name'], get_partitions(servers, ds_info))
        else:
            if not args.report_only and disc_threshold_exceeded(servers, args.threshold):
                # Remove all partitions of the
                # specified data where all the data is over
                # the specified age. If incremental deletes are
                # specified, check disc space after each delete,
                # and stop if below the disc threshold.
                ds_info = read_dataset_info(args.age_data, clickhouse)
                parts = get_partitions(servers, ds_info, args.max_age)
                if args.incremental:
                    while parts:
                        oldest = sorted(parts.keys())[0]
                        age_partitions(servers, { oldest: parts[oldest] }, args.force, args.dryrun)
                        del parts[oldest]
                        if parts and not disc_threshold_exceeded(servers, args.threshold):
                            break
                else:
                    age_partitions(servers, parts, args.force, args.dryrun)

        return 0

    except (PruneError, OSError, clickhouse_driver.errors.Error) as err:
        logging.error(err)
        print(err, file=sys.stderr)
        return 2
