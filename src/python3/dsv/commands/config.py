#!/usr/bin/env python3
#
# Copyright 2018-2019 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# A utility to obtain Visualizer config for use from non-Python worlds.

import random

description = 'get Visualizer configuration value.'

def add_args(parser):
    parser.add_argument('-r', '--random',
                        dest='random', action='store_true',
                        help='pick random entry from command separated list')
    parser.add_argument('cfg', nargs='+',
                        help='config key',
                        metavar='KEY')

def main(args, cfg):
    try:
        for conf in args.cfg:
            cfg = cfg[conf]
    except KeyError:
        return 1

    if args.random:
        print(random.choice(cfg.split(',')))
    else:
        print(cfg)
    return 0
