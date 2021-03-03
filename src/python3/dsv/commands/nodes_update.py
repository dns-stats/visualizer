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
# Update the Postgres nodes and attribute databases from nodes.csv.
#
# Usage: dsv-nodes-update <path-to-nodes.csv>
#

import csv
import socket
import sys

import psycopg2

import dsv.common.NodeFlag as dnf

description = 'update Postgres node information.'

class DSVNameError(Exception):
    pass

class EmptyNameError(DSVNameError):
    pass

class InvalidCharactersInNameError(DSVNameError):
    pass

class InvalidServiceAddrError(DSVNameError):
    pass

class SameNameError(DSVNameError):
    pass

class ServerNameAlreadyPresentError(DSVNameError):
    pass

class NodeNameAlreadyPresentError(DSVNameError):
    pass

class NotEnoughFieldsError(DSVNameError):
    pass

class InvalidVisibilityValue(DSVNameError):
    pass

def str_to_bool(s):
    return s.lower() not in ("no", "n", "false")

def check_name(name):
    if not name:
        raise EmptyNameError('Empty name.')
    for ch in name:
        if not (ch.isalnum() or ch in '.-'):
            raise InvalidCharactersInNameError('"{}" contains illegal name characters'.format(name))

def check_service_addr(addr):
    # Empty is allowed.
    if addr:
        try:
            socket.getaddrinfo(addr, 'domain', family=socket.AF_INET6)
        except socket.gaierror:
            try:
                socket.getaddrinfo(addr, 'domain')
            except socket.gaierror as e:
                raise InvalidServiceAddrError('Invalid service address {}'.format(addr)) from e

def name_pair(names):
    try:
        res = names.split('|', maxsplit=1)
        check_name(res[0])
        if len(res) < 2 or not res[1]:
            res = [res[0], None]
        else:
            check_name(res[1])
            if res[0] == res[1]:
                raise SameNameError('Primary and alternate names {} are the same'.format(res[0]))
        return tuple(res)
    except DSVNameError as err:
        print('Error in name pair {}.'.format(names), file=sys.stderr)
        raise err

VISIBILITY_VALUES = {
    'all':      dnf.NodeFlag.NONE.value,
    'test':     dnf.NodeFlag.HIDDEN.value,
    'main':     dnf.NodeFlag.HIDDEN_TEST.value,
    'none':     dnf.NodeFlag.HIDDEN.value | dnf.NodeFlag.HIDDEN_TEST.value,
}

def read_csv_remove_comments(f):
    for line in f:
        txt = line.split('#')[0].strip()
        if txt:
            yield txt

def read_csv(filename):
    with open(filename, newline='') as f:
        res = []
        for row in csv.reader(read_csv_remove_comments(f)):
            try:
                if len(row) < 6:
                    raise NotEnoughFieldsError('Server, name, region, country '
                                               'and city values are mandatory')

                # Each row is a node record. The record has the following
                # fields:
                # server, name, region, country, city, instance,
                # service address, visibility.
                #
                # Service address must be an IPv4 or IPv6 address, or
                # empty (i.e. no service address supplied).
                #
                # Visibility determines on which Grafana displays the node
                # will be included. It must be 'all', 'main', 'test',
                # 'none'. If left empty, it defaults to 'all'.
                #
                # The first 6 fields are compulsory. The last two may be
                # omitted, in which case they are treated as empty and
                # take the defaults.
                #
                # Each row is converted to a tuple of 8 values.
                # Each node record is a tuple:
                # (server, name, region, country, city, instance, IP, flags)
                # The flags field is an integer value of NodeFlag.
                server = row[0]
                name = row[1]
                region = row[2]
                country = row[3]
                city = row[4]
                instance = row[5]

                # Service address and flags fields may be legitimately
                # missing. Ensure there is at least an empty string for
                # each.
                row.extend(['', ''])
                service_addr = row[6]
                flags = dnf.NodeFlag.NONE.value
                if row[7]:
                    try:
                        flags |= VISIBILITY_VALUES[row[7].casefold()]
                    except KeyError as e:
                        raise InvalidVisibilityValue(row[7]) from e
                if not service_addr:
                    flags |= dnf.NodeFlag.NO_SERVICE_ADDR.value

                # Check names
                name_pair(server)
                name_pair(name)
                check_name(instance)
                if not region:
                    raise EmptyNameError('No region name')
                if not country:
                    raise EmptyNameError('No country name')
                if not city:
                    raise EmptyNameError('No city name')
                check_service_addr(service_addr)

                res.append((name, instance, server, city, country, region, service_addr, flags))
            except DSVNameError as err:
                print('Error in input {}.'.format(row[0:8]), file=sys.stderr)
                raise err

    return res

def find_server_id(cur, namepair):
    for name in namepair:
        if name:
            cur.execute('SELECT id FROM node_server '
                        'WHERE name=%(server)s OR altname=%(server)s',
                        {'server': name})
            res = cur.fetchone()
            if res:
                return res[0]
    return None

def check_server_names_unique(cur, server_id, namepair):
    # Ensure no name and altname clashes.
    if not server_id:
        server_id = 0   # Invalid server ID
    names = []
    cur.execute('SELECT name FROM node_server '
                'WHERE id<>%(server_id)s',
                {'server_id': server_id})
    for rec in cur:
        names.append(rec[0])
    cur.execute('SELECT altname FROM node_server '
                'WHERE id<>%(server_id)s AND altname IS NOT NULL',
                {'server_id': server_id})
    for rec in cur:
        names.append(rec[0])
    if namepair[0] in names:
        raise ServerNameAlreadyPresentError(
            'Server name "{}" already defined'.format(namepair[0]))
    if namepair[1] in names:
        raise ServerNameAlreadyPresentError(
            'Server altname "{}" already defined'.format(namepair[1]))

def find_node_id(cur, server_id, namepair):
    for name in namepair:
        if name:
            cur.execute('SELECT id FROM node '
                        'WHERE server_id=%(server_id)s '
                        'AND (name=%(node)s OR altname=%(node)s)',
                        {'node': name, 'server_id': server_id})
            res = cur.fetchone()
            if res:
                return res[0]
    return None

def check_node_names_unique(cur, server_id, node_id, namepair):
    # Ensure no name and altname clashes.
    if not node_id:
        node_id = 0   # Invalid node ID
    names = []
    cur.execute('SELECT name FROM node '
                'WHERE server_id=%(server_id)s AND id<>%(node_id)s',
                {'server_id': server_id, 'node_id': node_id})
    for rec in cur:
        names.append(rec[0])
    cur.execute('SELECT altname FROM node '
                'WHERE server_id=%(server_id)s AND id<>%(node_id)s '
                'AND altname IS NOT NULL',
                {'server_id': server_id, 'node_id': node_id})
    for rec in cur:
        names.append(rec[0])
    if namepair[0] in names:
        raise NodeNameAlreadyPresentError('Node name "{}" already defined'.format(namepair[0]))
    if namepair[1] in names:
        raise NodeNameAlreadyPresentError('Node altname "{}" already defined'.format(namepair[1]))

def add_attribute(cur, table, val):
    # Ensure 'val' name is present in table 'table'.
    cur.execute('INSERT INTO {} (name) VALUES (%s) '
                'ON CONFLICT (name) DO NOTHING'.format(table), (val,))

def add_all_attributes(cur, nodes, node_index, table):
    for n in nodes:
        add_attribute(cur, table, n[node_index])

def get_attr_index(cur, table, val):
    cur.execute('SELECT id FROM {} WHERE name = %s'.format(table), (val,))
    return cur.fetchone()[0]

def add_or_update_server(cur, names):
    namepair = name_pair(names)
    server_id = find_server_id(cur, namepair)
    check_server_names_unique(cur, server_id, namepair)
    if server_id:
        cur.execute('UPDATE node_server SET name=%s, altname=%s WHERE id=%s',
                    (namepair[0], namepair[1], server_id))
    else:
        cur.execute('INSERT INTO node_server(name, altname) VALUES (%s, %s)',
                    (namepair[0], namepair[1]))

def add_or_update_node(cur, node):
    node_names = name_pair(node[0])

    instance_id = get_attr_index(cur, 'node_instance', node[1])
    server_id = find_server_id(cur, name_pair(node[2]))
    city_id = get_attr_index(cur, 'node_city', node[3])
    country_id = get_attr_index(cur, 'node_country', node[4])
    region_id = get_attr_index(cur, 'node_region', node[5])
    service_addr = node[6]
    flags = node[7]

    node_id = find_node_id(cur, server_id, node_names)
    check_node_names_unique(cur, server_id, node_id, node_names)
    if node_id:
        cur.execute('UPDATE node '
                    'SET name=%s, instance_id=%s, server_id=%s, '
                    '    city_id=%s, country_id=%s, region_id=%s, '
                    '    service_addr=%s, altname=%s, flags=%s '
                    'WHERE id=%s',
                    (node_names[0], instance_id, server_id,
                     city_id, country_id, region_id,
                     service_addr, node_names[1], flags, node_id))
    else:
        cur.execute('INSERT INTO node(name, instance_id, server_id, '
                    '  city_id, country_id, region_id, '
                    '  service_addr, altname, flags) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (node_names[0], instance_id, server_id,
                     city_id, country_id, region_id,
                     service_addr, node_names[1], flags))

def mark_all_inactive(cur):
    cur.execute('UPDATE node SET flags=flags | %s', (dnf.NodeFlag.INACTIVE.value,))

def add_args(parser):
    parser.add_argument('nodesfile',
                        help='path to CVS file with node info',
                        metavar='NODEFILE')

def main(args, cfg):
    conn = None

    try:
        pgcfg = cfg['postgres']
        conn = psycopg2.connect(host=pgcfg['host'],
                                dbname=pgcfg['database'],
                                user=pgcfg['user'],
                                password=pgcfg['password'])

        nodes = read_csv(args.nodesfile)
        with conn.cursor() as cur:
            add_all_attributes(cur, nodes, 1, 'node_instance')
            add_all_attributes(cur, nodes, 3, 'node_city')
            add_all_attributes(cur, nodes, 4, 'node_country')
            add_all_attributes(cur, nodes, 5, 'node_region')

            for n in nodes:
                add_or_update_server(cur, n[2])

            # Set inactive flag on all records. Those updated from the
            # file will get their correct flags written, leaving all
            # nodes not in the CSV file marked inactive.
            mark_all_inactive(cur)

            for n in nodes:
                add_or_update_node(cur, n)

        conn.commit()
        conn.close()
        return 0
    except Exception:
        if conn is not None:
            conn.rollback()
            conn.close()
        raise
