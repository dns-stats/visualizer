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
# Freeze Visualizer import by removing write permission from the lock file.

import logging

import dsv.common.Lock as dl

description = 'freeze Visualizer import processing.'

def add_args(_):
    pass

def main(_, cfg):
    datastore_cfg = cfg['datastore']
    lock = dl.DSVLock(datastore_cfg['user'], datastore_cfg['lockfile'].format('import'))
    if lock.is_frozen():
        logging.info('Visualizer import freeze - already frozen.')
        print('Visualizer import already frozen.')
        return 1
    lock.freeze()
    logging.info('Visualizer import frozen.')
    print('Visualizer import frozen.')
    return 0
