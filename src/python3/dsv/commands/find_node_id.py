#!/usr/bin/env python3
#
# Copyright 2018-2020 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Find the node ID given server and node names.
#
# Usage: dsv-find-node-id <server-name> <node-name>
#

import psycopg2

description = 'find node ID from Postgres.'

def add_args(parser):
    parser.add_argument('servername',
                        help='the server name',
                        metavar='SERVERNAME')
    parser.add_argument('nodename',
                        help='the node name',
                        metavar='NODENAME')

def main(args, cfg):
    conn = None

    try:
        pgcfg = cfg['postgres']
        conn = psycopg2.connect(host=pgcfg['host'],
                                dbname=pgcfg['database'],
                                user=pgcfg['user'],
                                password=pgcfg['password'])

        with conn.cursor() as cur:
            cur.execute('SELECT node.id FROM node '
                        'INNER JOIN node_server ON node_server.id = node.server_id '
                        'WHERE (node_server.name=%(server)s OR '
                        '       node_server.altname=%(server)s) '
                        'AND (node.name=%(node)s OR node.altname=%(node)s)',
                        {'server': args.servername, 'node': args.nodename})
            res = cur.fetchone()

        conn.close()

        if res:
            print(res[0])
            return 0
        return 1
    except Exception:
        if conn is not None:
            conn.rollback()
            conn.close()
        raise
