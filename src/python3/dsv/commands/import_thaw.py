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
# Thaw Visualizer import by adding write permission to the lock file.

import logging

import dsv.common.Lock as dl

description = 'thaw Visualizer import processing.'

def add_args(_):
    pass

def main(_, cfg):
    datastore_cfg = cfg['datastore']
    lock = dl.DSVLock(datastore_cfg['user'], datastore_cfg['lockfile'].format('import'))
    if not lock.is_frozen():
        logging.info('Visualizer import thaw - already thawed.')
        print('Visualizer import already thawed.')
        return 1
    lock.thaw()
    logging.info('Visualizer import thawed.')
    print('Visualizer import thawed.')
    return 0
