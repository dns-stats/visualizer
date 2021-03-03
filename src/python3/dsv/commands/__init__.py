#!/usr/bin/env python3
#
# Copyright 2018-2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Start a program from dsv.commands depending on contents of argv[0].

import argparse
import pathlib
import sys
import traceback
import importlib.util

import dsv.common.Config as dc

def module_name(cmd):
    return 'dsv.commands.' + cmd.replace('-', '_')

def available_commands():
    res = []
    for pentry in sys.path:
        cmddir = pathlib.Path(pentry) / 'dsv' / 'commands'
        if cmddir.is_dir():
            for mod in cmddir.glob('*.py'):
                name = mod.stem
                if name and name[0] != '_' and \
                   importlib.util.spec_from_file_location(module_name(name), str(mod)):
                    res.append(name.replace('_', '-'))
    return sorted(res)

def run_command(cmd, argv):
    exe = importlib.import_module(module_name(cmd))

    parser = argparse.ArgumentParser(description=exe.description)
    parser.add_argument('-c', '--config',
                        dest='conf_file', action='store', default=None,
                        help='configuration file location',
                        metavar='CONFIG_FILE')
    parser.add_argument('--traceback',
                        dest='traceback', action='store_true',
                        help=argparse.SUPPRESS)
    exe.add_args(parser)
    args = parser.parse_args(argv[1:])
    cfg = dc.Config(args.conf_file)
    try:
        return exe.main(args, cfg)
    except Exception as e:
        if args.traceback:
            traceback.print_exc()
        raise e
