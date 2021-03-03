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
# Add a job to a Visualizer queue.

import datetime
import sys

import dsv.common.DateTime as dd
import dsv.common.Queue as dq

description = 'add a job to a processing queue.'

def add_args(parser):
    parser.add_argument('-q', '--queue',
                        dest='queue', action='store',
                        choices=['cdns-to-tsv', 'cdns-to-pcap', 'import-tsv'],
                        required=True,
                        help='the queue to use - cdns-to-tsv, cdns-to-pcap or import-tsv',
                        metavar='QUEUE')
    parser.add_argument('--not-before',
                        dest='notbefore', action='store',
                        type=dd.arg_valid_date_type,
                        default=None,
                        help='don\'t execute job before this date/time',
                        metavar='DATETIME')
    parser.add_argument('--delay',
                        dest='delay', type=int, action='store',
                        default=None,
                        help='delay for SECS before executing job',
                        metavar='SECS')
    parser.add_argument('jobs',
                        nargs='+',
                        help='the job string to add to the queue',
                        metavar='JOB')

def main(args, cfg):
    if args.delay and args.notbefore:
        print('Only one of --delay and --notbefore is allowed.', file=sys.stderr)
        return 1

    if args.delay:
        notbefore = datetime.datetime.now() + datetime.timedelta(seconds=args.delay)
    else:
        notbefore = args.notbefore
    with dq.QueueContext(cfg, sys.argv[0]).writer() as writer:
        for job in args.jobs:
            writer.add(args.queue, job, notbefore=notbefore)
    return 0
