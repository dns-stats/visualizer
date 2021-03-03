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
# Freeze Visualizer queue execution by removing write permission from the lock file.

import logging

import dsv.common.Lock as dl

description = 'freeze Visualizer queue processing.'

def add_args(parser):
    parser.add_argument('queue', nargs='+',
                        help='queue name',
                        metavar='QUEUE')

def main(args, cfg):
    datastore_cfg = cfg['datastore']
    exit_status = 0
    for q in args.queue:
        if q not in datastore_cfg['queues']:
            logging.error('{}: no such queue.'.format(q))
            print('{}: no such queue.'.format(q))
            exit_status = 1
            continue

        lock = dl.DSVLock(datastore_cfg['user'], datastore_cfg['lockfile'].format(q))
        if lock.is_frozen():
            logging.info('Visualizer queue {} freeze - already frozen.'.format(q))
            print('Visualizer queue {} already frozen.'.format(q))
            exit_status = 1
            continue
        lock.freeze()
        logging.info('Visualizer queue {} frozen.'.format(q))
        print('Visualizer queue {} frozen.'.format(q))
    return exit_status
