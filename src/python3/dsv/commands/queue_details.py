#!/usr/bin/env python3
#
# Copyright 2018-2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Scan Visualizer incoming directories reporting on current sizes of the
# C-DNS-TSV, TSV import queue and the number of entries in each
# error directory.
#
# The reports can be either printed to stdout or posted to
# a ClickHouse table.

import datetime
import logging
import pathlib
import random
import sys

import psycopg2

import clickhouse_driver
import clickhouse_driver.errors

import dsv.common.Path as dp

description = 'report on queue sizes and number of error files'

def find_node_id(cur, server_name, node_name):
    cur.execute('SELECT node.id FROM node '
                'INNER JOIN node_server ON node_server.id = node.server_id '
                'WHERE (node_server.name=%(server)s OR '
                '       node_server.altname=%(server)s) '
                'AND (node.name=%(node)s OR node.altname=%(node)s)',
                {'server': server_name, 'node': node_name})
    res = cur.fetchone()
    return res[0] if res else None

def count_files(path, dir_pattern, file_pattern):
    """Count files by server/hostname matching the pattern.

       Files matching file_pattern are selected from directories
       under path matching dir_pattern.

       The directory structure is path/<service>/<hostname>/<dir>/<file>.

       Return dictionary of servers, each with dictionary of hostnames
       containing the number of files for that server/hostname."""
    res = {}
    for dpath in pathlib.Path(path).glob('*/*/' + dir_pattern):
        if dpath.is_dir():
            wompath = dp.DSVPath(dpath)
            if wompath.server not in res:
                res[wompath.server] = {}
            res[wompath.server][wompath.node] = sum(1 for _ in dpath.glob(file_pattern))
    return res

def count_pending_files(path, dir_pattern, file_pattern):
    return count_files(path, dir_pattern + '/' + dp.PENDING_DIR, file_pattern)

def count_error_files(path, queue, file_pattern):
    return count_files(path, dp.error_dir_base_name(queue), file_pattern)

def count(info, server, node):
    return info[server][node] if server in info and node in info[server] else 0

def print_node_info(node_info):
    max_servername_len = 0
    max_nodename_len = 0
    for server in node_info.keys():
        max_servername_len = max(max_servername_len, len(server))
        for node in node_info[server].keys():
            max_nodename_len = max(max_nodename_len, len(node))

    line_fmt = (
        '| {{server:{server_len}}} | {{node:{node_len}}} '
        '| {{node_id!s:>5}} | {{cdns_incoming:>5}} '
        '| {{cdns_pending:>5}} | {{tsv_pending:>5}} | {{pcap_pending:>5}} '
        '| {{err_cdns_incoming:>5}} | {{err_tsv:>5}} | {{err_cdns_pcap:>5}} |'
    ).format(
        server_len=max_servername_len,
        node_len=max_nodename_len)
    sep_fmt = (
        '+' + ''.ljust(max_servername_len + 2, '-') +
        '+' + ''.ljust(max_nodename_len + 2, '-') +
        '+-------+-------'
        '+-------+-------+-------'
        '+-------+-------+-------+'
    )

    print(sep_fmt)
    print(line_fmt.format(server='Server', node='Node', node_id='Node',
                          cdns_incoming='CDNS', cdns_pending='CDNS',
                          tsv_pending='TSV', pcap_pending='PCAP',
                          err_cdns_incoming='CDNS', err_tsv='TSV',
                          err_cdns_pcap='PCAP'))
    print(line_fmt.format(server='', node='', node_id='ID',
                          cdns_incoming='incom', cdns_pending='pend',
                          tsv_pending='pend', pcap_pending='pend',
                          err_cdns_incoming='errs', err_tsv='errs',
                          err_cdns_pcap='errs'))
    print(sep_fmt)
    for server in sorted(node_info.keys()):
        for node in sorted(node_info[server].keys()):
            n = node_info[server][node]
            print(line_fmt.format(server=server, node=node, node_id=n[0],
                                  cdns_incoming=n[1], cdns_pending=n[2],
                                  tsv_pending=n[3], pcap_pending=n[4],
                                  err_cdns_incoming=n[5], err_tsv=n[6],
                                  err_cdns_pcap=n[7]))
    print(sep_fmt)

def store_node_info(node_info, ch_client):
    values = []
    now = datetime.datetime.now()
    for server in node_info:
        for node in node_info[server]:
            n = node_info[server][node]
            if n[0] is not None:
                values.append({'Date': now.date(),
                               'DateTime': now,
                               'NodeID': n[0],
                               'CDNSIncoming': n[1],
                               'CDNStoTSVPending': n[2],
                               'TSVImportPending': n[3],
                               'CDNStoPCAPPending': n[4],
                               'CDNStoTSVErrors': n[5],
                               'TSVImportErrors': n[6],
                               'CDNStoPCAPErrors': n[7]})
    if values:
        ch_client.execute(
            'INSERT INTO dsv.ImportQueueSizes(Date, DateTime, NodeID, '
            'CDNSIncoming, CDNStoTSVPending, TSVImportPending, '
            'CDNStoPCAPPending,  CDNStoTSVErrors, TSVImportErrors, '
            'CDNStoPCAPErrors) VALUES',
            values)

def add_args(parser):
    parser.add_argument('-p', '--print',
                        dest='print', action='store_true', default=False,
                        help='print report on queue sizes')
    parser.add_argument('-s', '--store',
                        dest='store', action='store_true', default=False,
                        help='write queue sizes to ClickHouse')

def main(args, cfg):
    # pylint: disable=too-many-locals
    datastore_cfg = cfg['datastore']
    path_base = datastore_cfg['path']
    cdns_file_pattern = datastore_cfg['cdns_file_pattern']
    tsv_file_pattern = datastore_cfg['tsv_file_pattern']

    cdns_incoming = count_files(path_base, dp.INCOMING_DIR, cdns_file_pattern)
    cdns_pending = count_pending_files(path_base, dp.INCOMING_DIR, cdns_file_pattern)
    tsv_pending = count_pending_files(path_base, dp.INCOMING_DIR, tsv_file_pattern)
    pcap_pending = count_pending_files(path_base, dp.PCAP_DIR, cdns_file_pattern)
    error_cdns_to_tsv = count_files(path_base, 'cdns-to-tsv', cdns_file_pattern)
    error_import_tsv = count_files(path_base, 'import-tsv', tsv_file_pattern)
    error_cdns_to_pcap = count_files(path_base, 'cdns-to-pcap', cdns_file_pattern)

    # Collect into server/node dict, but each data item is a tuple
    # containing (node id, CDNS incoming, CDNS pending, TSV pending,
    # PCAP pening, CDNS-TSV error, TSV error, CDNS-PCAP error).
    # If node lookup fails, node id is None.
    #
    # Watch out for missing servers and nodes. If there is no instance
    # of a directory in a node, we won't have a record, and if there's
    # no instance in a server (e.g. a server with a few nodes that's
    # never had an error), we won't even have a server record.
    node_info = {}
    conn = None
    try:
        pgcfg = cfg['postgres']
        conn = psycopg2.connect(host=pgcfg['host'],
                                dbname=pgcfg['database'],
                                user=pgcfg['user'],
                                password=pgcfg['password'])

        with conn.cursor() as cur:
            for server in cdns_incoming:
                if server not in node_info:
                    node_info[server] = {}
                for node in cdns_incoming[server]:
                    node_id = find_node_id(cur, server, node)
                    if node_id is None:
                        logging.warning('Server {server} node {node} not found in nodes.csv'.format(
                            server=server, node=node))
                    node_info[server][node] = (
                        node_id,
                        count(cdns_incoming, server, node),
                        count(cdns_pending, server, node),
                        count(tsv_pending, server, node),
                        count(pcap_pending, server, node),
                        count(error_cdns_to_tsv, server, node),
                        count(error_import_tsv, server, node),
                        count(error_cdns_to_pcap, server, node),
                    )
    except Exception:
        if conn is not None:
            conn.rollback()
            conn.close()
        raise

    if args.print:
        print_node_info(node_info)

    if args.store:
        clickhouse = cfg['clickhouse']
        ch_server = random.choice(clickhouse['servers'].split(',')).strip()
        ch_user = clickhouse['user']
        ch_pass = clickhouse['password']
        logging.debug('Using ClickHouse server {}'.format(ch_server))

        try:
            ch_client = clickhouse_driver.Client(host=ch_server, user=ch_user, password=ch_pass)
            store_node_info(node_info, ch_client)
        except (OSError, clickhouse_driver.errors.Error) as err:
            logging.error(err)
            print(err, file=sys.stderr)
            return 1

    return 0
