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
# Get Visualizer queue status info

import sys

import dsv.common.Lock as dl
import dsv.common.Queue as dq

description = 'get queue status.'

def add_args(parser):
    parser.add_argument('-q', '--queue',
                        dest='queue', action='store',
                        choices=['cdns-to-tsv', 'cdns-to-pcap', 'import-tsv'],
                        default=None,
                        help='the queue to use - cdns-to-tsv, cdns-to-pcap or import-tsv',
                        metavar='QUEUE')
    parser.add_argument('items',
                        nargs='*',
                        help='the status item to show (len, running, workers, frozen)',
                        metavar='ITEM')

def main(args, cfg):
    datastore_cfg = cfg['datastore']

    ctx = dq.QueueContext(cfg, sys.argv[0])
    for q in ctx.status():
        if args.queue:
            if args.queue != q[0]:
                continue
        qinfo = {'name': q[0], 'len': q[1], 'running': q[2], 'workers': q[3]}
        lock = dl.DSVLock(datastore_cfg['user'], datastore_cfg['lockfile'].format(q[0]))
        qinfo['frozen'] = 'frozen' if lock.is_frozen() else 'active'
        if args.items:
            first = True
            for item in args.items:
                try:
                    if first:
                        first = False
                    else:
                        print(',', end='')
                    print(qinfo[item], end='')
                except KeyError:
                    print('Unknown item {} - use len, running, '
                          'workers or frozen'.format(item), file=sys.stderr)
                    return 1
            print()
        else:
            print('{queue}: {items} queued, {running} running, '
                  '{workers} workers, {frozen}'.format(
                      queue=qinfo['name'], items=qinfo['len'],
                      running=qinfo['running'], workers=qinfo['workers'],
                      frozen=qinfo['frozen']))
    return 0
