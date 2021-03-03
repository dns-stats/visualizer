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
# Thaw Visualizer queue execution by adding write permission from the lock file.

import logging

import dsv.common.Lock as dl

description = 'Thaw Visualizer queue processing.'

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
        if not lock.is_frozen():
            logging.info('Visualizer queue {} thaw - already thawed.'.format(q))
            print('Visualizer queue {} already thawed.'.format(q))
            exit_status = 1
            continue
        lock.thaw()
        logging.info('Visualizer queue {} thawed.'.format(q))
        print('Visualizer queue {} thawed.'.format(q))
    return exit_status
