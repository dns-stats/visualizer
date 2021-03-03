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
# A utility to log text via Visualizer logging for use from non-Python worlds.

import logging

description = 'get Visualizer configuration value.'

def add_args(parser):
    parser.add_argument('-l', '--level',
                        dest='level', action='store',
                        choices=['critical', 'error', 'warning', 'info', 'debug'],
                        default='info',
                        help='log level: critical, error, warning, info (default), debug',
                        metavar='LEVEL')
    parser.add_argument('txt', nargs='*',
                        help='text to log',
                        metavar='TEXT')

def main(args, _):
    txt = " ".join(args.txt)
    for lvl in (logging.CRITICAL, logging.ERROR, logging.WARNING,
                logging.INFO, logging.DEBUG):
        if logging.getLevelName(lvl).lower() == args.level:
            logging.log(lvl, txt)
            return 0
    return 1
