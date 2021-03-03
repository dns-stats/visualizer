# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import logging
import pathlib
import re
import sys

ACTION_APPLY = 0
ACTION_ROLLBACK = 1

DDL_RE = re.compile(r"[0-9]+\.sql")
DDL_ROLLBACK_RE_FORMAT = r"0*{}\-rollback\.sql"

class DDLActions:
    def apply_ddl(self, ddl_file, version, action=ACTION_APPLY):
        """Action the DDL file as the given version and action type.

        Action types are apply or rollback. Once the DDL is applied,
        also record the version, date/time and action type in the DDL
        history."""
        raise NotImplementedError

    def read_ddl_info(self, ddl_path):
        """Return DDL action history - list of (version, date/time of action, action).

        This method should read the DDL history table. If not
        present, it should create it and return an empty history."""
        raise NotImplementedError

def ddl_files_matching_re(ddl_path, re):
    # Globbing is too imprecise to pick the exact files.
    return sorted([f for f in ddl_path.glob('*.sql') if re.fullmatch(f.name)])

def ddl_files(ddl_path):
    return ddl_files_matching_re(ddl_path, DDL_RE)

def ddl_rollback_files(ddl_path, version):
    return ddl_files_matching_re(ddl_path, re.compile(DDL_ROLLBACK_RE_FORMAT.format(version)))

def active_ddls(ddl_info):
    res = {}
    for ddl in ddl_info:
        if ddl[2]:
            del res[ddl[0]]
        else:
            res[ddl[0]] = ddl[1]
    return res

def apply(ddl_actions, ddl_info, ddl_path, args):
    active = active_ddls(ddl_info)

    for ddl_file in ddl_files(ddl_path):
        ver = int(ddl_file.stem)
        if ver not in active:
            if not args.dry_run:
                ddl_actions.apply_ddl(ddl_file, ver, ACTION_APPLY)
                if not args.quiet:
                    print('Applied {}.'.format(ver))
            else:
                if not args.quiet:
                    print('Dry run - apply {}.'.format(ver))
        else:
            if args.verbose and not args.quiet:
                print('Skipping {}, already applied.'.format(ver))
    return 0

def rollback(ddl_actions, ddl_info, ddl_path, args):
    active = active_ddls(ddl_info)
    if active:
        top = sorted(active.keys())[-1]
        ddl_files = ddl_rollback_files(ddl_path, top)
        if ddl_files:
            for ddl_file in ddl_files:
                if not args.dry_run:
                    ddl_actions.apply_ddl(ddl_file, top, ACTION_ROLLBACK)
                    if not args.quiet:
                        print('Rolled back {}.'.format(top))
                else:
                    if not args.quiet:
                        print('Dry run - roll back {}.'.format(top))
            return 0
        else:
            if not args.quiet:
                print('No rollback available for {}.'.format(top))
            return 1
    else:
        if not args.quiet:
            print('No DDLs applied.')
        return 0

def status(ddl_info, ddl_path, args):
    active = active_ddls(ddl_info)
    if not args.quiet:
        if args.verbose:
            for ddl in ddl_info:
                print('{ddl:5} {verb} at {time}'.format(
                    ddl=ddl[0],
                    verb='rollback' if ddl[2] else ' applied',
                    time=ddl[1]))
        else:
            ddls = sorted(active.keys())
            if len(ddls) > args.last:
                print('Limiting output to last {} items.'.format(args.last))
                ddls = ddls[-args.last:]
            for ddl in ddls:
                print('{ddl:5} applied at {time}'.format(
                    ddl=ddl,
                    time=active[ddl]))
    res = 0
    for ddl_file in ddl_files(ddl_path):
        ver = int(ddl_file.stem)
        if ver not in active:
            res = 1
            if not args.quiet:
                print('{:5} to be applied.'.format(ver))
    return res

def add_args(parser):
    parser.add_argument('-r', '--update-required',
                        dest='req_update', action='store_true', default=False,
                        help='just check whether an update is required')
    parser.add_argument('-v', '--verbose',
                        action='store_true', default=False,
                        help='produce more detailed output messages')
    parser.add_argument('-q', '--quiet',
                        action='store_true', default=False,
                        help='disable output messages')
    parser.add_argument('-a', '--action',
                        dest='action', action='store', default='update',
                        choices=['update', 'rollback', 'status'],
                        help='update, rollback or status',
                        metavar='ACTION')
    parser.add_argument('-l', '--last',
                        dest='last', action='store', type=int, default=10,
                        help='list last N items only, default 10',
                        metavar='N')
    parser.add_argument('-n', '--dry-run',
                        dest='dry_run', action='store_true', default=False,
                        help='perform a trial run')
    parser.add_argument('ddl_path',
                        nargs='?', default=None,
                        help='path to directory with DDL files',
                        metavar='DDLPATH')

def main(args, ddl_actions):
    ddl_path = pathlib.Path(args.ddl_path)

    if args.req_update:
        if args.action != 'update':
            print("--update-required only valid with action 'update'.", file=sys.stderr)
            return 2
        args.action = 'status'
        args.quiet = True

    try:
        ddl_info = ddl_actions.read_ddl_info(ddl_path)

        if args.action == 'update':
            return apply(ddl_actions, ddl_info, ddl_path, args)
        elif args.action == 'rollback':
            return rollback(ddl_actions, ddl_info, ddl_path, args)
        else:
            return status(ddl_info, ddl_path, args)
    except Exception as e:
        logging.error('Exception {exc} ({args})'.format(
            exc=type(e).__name__,
            args=str(e)))
        print('Error {exc} ({args}).'.format(
            exc=type(e).__name__,
            args=str(e)), file=sys.stderr)
        return 2
