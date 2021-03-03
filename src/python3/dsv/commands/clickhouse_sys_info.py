#!/usr/bin/env python3
#
# Copyright 2019 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Return data on a Visualizer database server. Intended for use with a
# ClickHouse dictionary with a complex key, so listens on stdin for
# the names of keys and outputs key\tvalue in reply.
#
# Usage: dsv-clickhouse-sys-info [-c|--config conf_file]
#
# Keys recognised: disc-block-size, disc-size, disc-available,
#                  disc-percent-free, disc-percent-used
#

import logging
import os
import sys

description = 'read keys from stdin, return system quantities.'

def add_args(_):
    pass

def main(_, cfg):
    statfs = os.statvfs(cfg['clickhouse']['dbdir'])

    for line in sys.stdin.readlines():
        line = line.strip()
        if line == 'disc-block-size':
            val = statfs.f_bsize
        elif line == 'disc-size':
            val = statfs.f_blocks * statfs.f_frsize // 1024
        elif line == 'disc-available':
            val = statfs.f_bavail * statfs.f_frsize // 1024
        elif line == 'disc-percent-free':
            val = 100 *statfs.f_bavail // statfs.f_blocks
        elif line == 'disc-percent-used':
            val = 100 - (100 * statfs.f_bavail // statfs.f_blocks)
        else:
            print('Unknown key: {key}'.format(key=line))
            logging.error('Unknown key: {key}'.format(key=line))
            return 1

        print('{key}\t{val}'.format(key=line, val=val))
    return 0
