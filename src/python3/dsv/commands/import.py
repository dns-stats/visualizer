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
# Scan Visualizer incoming directories looking for new C-DNS files (.cbor.xz)
# that have not yet been added to the list for processing, and add them.

import logging
import os
import os.path
import pathlib
import sys

import dsv.common.DateTime as dd
import dsv.common.Lock as dl
import dsv.common.Path as dp
import dsv.common.Queue as dq

description = 'check for files and add to processing queue.'

INCOMING_DIR_PATTERN = '*/*/' + dp.INCOMING_DIR
CDNS_DIR_PATTERN = '*/*/' + dp.CDNS_DIR
PCAP_DIR_PATTERN = '*/*/' + dp.PCAP_DIR

def error_dir_pattern(queue_name):
    return '*/*/' + dp.error_dir_base_name(queue_name)

class ExcludeInclude:
    def __init__(self):
        self._exclude = []
        self._include = []

    def add_include(self, item):
        self._include.extend(item)

    def add_exclude(self, item):
        self._exclude.extend(item)

    def use(self, item):
        if self._include:
            return item in self._include
        return item not in self._exclude

class Filter:
    # pylint: disable=too-many-branches,too-many-statements
    def __init__(self, server_dir):
        self._nodes_pcap = ExcludeInclude()
        self._nodes_import = ExcludeInclude()
        self._servers_pcap = ExcludeInclude()
        self._servers_import = ExcludeInclude()
        self._start = None
        self._end = None
        self._default_pcap = False

        f = server_dir / 'dsv.filter'
        if not f.exists():
            f = server_dir / 'inspector.filter'
        if f.exists():
            with open(str(f)) as fd:
                for line in fd:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    cmd, _, arg = line.partition(' ')
                    cmd = cmd.strip().lower()
                    arg = arg.strip()
                    args = arg.split()
                    if cmd == 'exclude_node':
                        self._nodes_pcap.add_exclude(args)
                        self._default_pcap = True
                    elif cmd == 'include_node':
                        self._nodes_pcap.add_include(args)
                        self._default_pcap = True
                    elif cmd == 'exclude_import':
                        self._nodes_import.add_exclude(args)
                    elif cmd == 'include_import':
                        self._nodes_import.add_include(args)
                    elif cmd == 'exclude_server':
                        self._servers_pcap.add_exclude(args)
                        self._default_pcap = True
                    elif cmd == 'include_server':
                        self._servers_pcap.add_include(args)
                        self._default_pcap = True
                    elif cmd == 'exclude_server_import':
                        self._servers_import.add_exclude(args)
                    elif cmd == 'include_server_import':
                        self._servers_import.add_include(args)
                    elif cmd == 'start_date':
                        self._start = dd.parse_datetime(arg)
                        self._default_pcap = True
                    elif cmd == 'end_date':
                        self._end = dd.parse_datetime(arg)
                        self._default_pcap = True
                    elif cmd == 'enable_pcap':
                        self._default_pcap = True
                    else:
                        raise ValueError('Unknown filter: {}'.format(cmd))
                    # By default, if no PCAP commands are present, no PCAP
                    # is generated. If a single PCAP related command is
                    # present, then the default changes: PCAP is always
                    # generated unless otherwise specified (i.e. by
                    # a node being excluded or a date range being given).
            if self._start and self._end and (self._start >= self.end):
                raise ValueError('{}: Filter end time must be after start time.'.format(str(f)))

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def default_pcap(self):
        return self._default_pcap

    def use_node_pcap(self, node):
        return self._nodes_pcap.use(node)

    def use_node_import(self, node):
        return self._nodes_import.use(node)

    def use_server_pcap(self, server):
        return self._servers_pcap.use(server)

    def use_server_import(self, server):
        return self._servers_import.use(server)

server_filters = {}

def link(file_path, target_path):
    """Link file to the target name.

       Ensure that the target directory exists. If target file already exists,
       log warning and return False.
    """
    if target_path.exists():
        logging.warning('link target {} exists'.format(str(target_path)))
        return False
    target_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        # If origin file has been deleted between assembling the list
        # and actioning it, this will fail.
        os.link(str(file_path), str(target_path))
        return True
    except FileNotFoundError as err:
        logging.warning(err)
        return False

def files_to_process(path, dir_pattern, file_pattern, from_date=None, to_date=None):
    """Generate list of files in processing order.

       Files matching file_pattern are selected from directories
       under path matching dir_pattern. If from_date is given,
       the file date must be >= from_date. If to_date is given,
       the file date must be < to_date.

       The directory structure is path/<service>/<hostname>/<dir>/<file>.

       For each server we encounter, ensure its filters are loaded.

       To prevent files from a single host blocking timely processing
       of less busy hosts, take one file from each directory at a time."""
    nodefiles = {}
    for dpath in pathlib.Path(path).glob(dir_pattern):
        if dpath.is_dir():
            wompath = dp.DSVPath(dpath)
            node = wompath.server + '|' + wompath.node
            nodefiles[node] = []
            for f in dpath.glob(file_pattern):
                fpath = dp.DSVPath(f)
                if fpath.server not in server_filters:
                    server_filters[fpath.server] = Filter(fpath.server_dir_path)
                if from_date or to_date:
                    if from_date and fpath.datetime() < from_date:
                        continue
                    if to_date and fpath.datetime() >= to_date:
                        continue
                nodefiles[node].append(str(f))
    # Put node files in reverse path order - so in reverse date order,
    # most recent first.
    for node in nodefiles:
        nodefiles[node].sort(reverse=True)
    more = True
    while more:
        more = False
        for node in nodefiles:
            if len(nodefiles[node]) > 0:
                yield nodefiles[node].pop(0)
                more = True

def assess_pcap_filter(filt, dsv_file_path, check_time=True):
    if check_time and (filt.start or filt.end):
        datim = dsv_file_path.datetime()
        if filt.start and datim < filt.start:
            return False
        if filt.end and datim >= filt.end:
            return False
    if filt.use_node_pcap(dsv_file_path.node) and filt.use_server_pcap(dsv_file_path.server):
        return True
    return False

def generate_pcap_import(dsv_file_path):
    local_filter = server_filters[dsv_file_path.server]
    global_filter = server_filters[None]
    local_filt_res = assess_pcap_filter(local_filter, dsv_file_path)
    global_filt_res = assess_pcap_filter(global_filter, dsv_file_path)

    # If passes both filters, check the PCAP default on both. If either
    # is to generate, we generate.
    if local_filt_res and global_filt_res:
        return local_filter.default_pcap or global_filter.default_pcap

    return False

def generate_pcap_manual(dsv_file_path):
    local_filter = server_filters[dsv_file_path.server]
    global_filter = server_filters[None]
    local_filt_res = assess_pcap_filter(local_filter, dsv_file_path, False)
    global_filt_res = assess_pcap_filter(global_filter, dsv_file_path, False)
    return local_filt_res and global_filt_res

def do_import(dsv_file_path):
    local_filter = server_filters[dsv_file_path.server]
    global_filter = server_filters[None]
    return \
        local_filter.use_node_import(dsv_file_path.node) and \
        local_filter.use_server_import(dsv_file_path.server) and \
        global_filter.use_node_import(dsv_file_path.node) and \
        global_filter.use_server_import(dsv_file_path.server)

def process_incoming(writer, path, file_pattern, verbose, dryrun):
    """Process incoming jobs.

       Run over C-DNS in */incoming and:

       1. Link to incoming/pending and submit convert to TSV job.
       2. If required, link to pcap/pending and submit convert PCAP job.
       3. Move file from incoming to cbor.

       Return number of files queued.
    """
    res = 0
    for f in files_to_process(path, INCOMING_DIR_PATTERN, file_pattern):
        fpath = dp.DSVPath(f)
        if do_import(fpath):
            if verbose:
                print('Add {} to cdns-to-tsv'.format(f))
            if dryrun:
                res += 1
            else:
                pendingpath = fpath.incoming_pending_file_path
                if link(fpath.incoming_file_path, pendingpath):
                    writer.add('cdns-to-tsv', pendingpath)
                    res += 1

        if generate_pcap_import(fpath):
            if verbose:
                print('Add {} to cdns-to-pcap'.format(f))
            if dryrun:
                res += 1
            else:
                pendingpath = fpath.pcap_pending_file_path
                if link(fpath.incoming_file_path, pendingpath):
                    writer.add('cdns-to-pcap', pendingpath, dq.JobPrecedence.low)
                    res += 1

        if not dryrun:
            cdnspath = fpath.cdns_file_path
            cdnspath.parent.mkdir(parents=True, exist_ok=True)
            try:
                # If origin file has been deleted between assembling the list
                # and actioning it, this will fail.
                fpath.incoming_file_path.rename(cdnspath)
            except FileNotFoundError as err:
                logging.warning(err)
    return res

def process_cbor(writer, path, file_pattern, from_date, to_date, verbose, dryrun):
    """Process loading from cbor directory.

       Run over C-DNS in */cbor and, for file in-date and node not import filtered:

       1. Link to cbor/pending and submit low priority convert to TSV job.

       Return number of files queued.
    """
    res = 0
    for f in files_to_process(path, CDNS_DIR_PATTERN, file_pattern, from_date, to_date):
        fpath = dp.DSVPath(f)
        if do_import(fpath):
            if verbose:
                print('Add {} to cdns-to-tsv'.format(f))
            if dryrun:
                res += 1
            else:
                pendingpath = fpath.cdns_pending_file_path
                if link(fpath.cdns_file_path, pendingpath):
                    writer.add('cdns-to-tsv', pendingpath, dq.JobPrecedence.low)
                    res += 1
    return res

def process_pcap(writer, path, file_pattern, from_date, to_date, verbose, dryrun):
    """Process generating PCAP from cbor directory.

       Run over C-DNS in */cbor and, for file in-date and node not PCAP filtered:

       1. Link to pcap/pending and submit low priority convert to PCAP job.

       Return number of files queued.
    """
    res = 0
    for f in files_to_process(path, CDNS_DIR_PATTERN, file_pattern, from_date, to_date):
        fpath = dp.DSVPath(f)
        if generate_pcap_manual(fpath):
            if verbose:
                print('Add {} to cdns-to-pcap'.format(f))
            if dryrun:
                res += 1
            else:
                pendingpath = fpath.pcap_pending_file_path
                if link(fpath.cdns_file_path, pendingpath):
                    writer.add('cdns-to-pcap', pendingpath, dq.JobPrecedence.low)
                    res += 1
    return res

def process_error(writer, path,
                  cdns_file_pattern, tsv_file_pattern, verbose, dryrun):
    """Refill queue from error directories. Return count."""
    res = 0
    for f in files_to_process(path, error_dir_pattern('cdns-to-tsv'), cdns_file_pattern):
        fpath = dp.DSVPath(f)
        if verbose:
            print('Add {} to cdns-to-tsv'.format(f))
        if dryrun:
            res += 1
        else:
            pendingpath = fpath.incoming_pending_file_path
            if link(fpath.error_file_path('cdns-to-tsv'), pendingpath):
                writer.add('cdns-to-tsv', pendingpath)
                res += 1
                fpath.path.unlink()

    for f in files_to_process(path, error_dir_pattern('cdns-to-pcap'), cdns_file_pattern):
        fpath = dp.DSVPath(f)
        if verbose:
            print('Add {} to cdns-to-pcap'.format(f))
        if dryrun:
            res += 1
        else:
            pendingpath = fpath.incoming_pending_file_path
            if link(fpath.error_file_path('cdns-to-pcap'), pendingpath):
                writer.add('cdns-to-pcap', pendingpath)
                res += 1
                fpath.path.unlink()

    for f in files_to_process(path, error_dir_pattern('import-tsv'), tsv_file_pattern):
        fpath = dp.DSVPath(f)
        if verbose:
            print('Add {} to import-tsv'.format(f))
        if dryrun:
            res += 1
        else:
            pendingpath = fpath.incoming_pending_file_path
            if link(fpath.error_file_path('import-tsv'), pendingpath):
                writer.add('import-tsv', pendingpath)
                res += 1
                fpath.path.unlink()

    return res

def process_regen_tsv(writer, path,
                      cdns_file_pattern, tsv_file_pattern, verbose, dryrun):
    """Refill C-DNS queue from failures in TSV error directories. Return count."""
    res = 0
    for f in files_to_process(path, error_dir_pattern('import-tsv'), tsv_file_pattern):
        fpath = dp.DSVPath(f)
        # Look for original C-DNS.
        fname = pathlib.Path(fpath.path.name)
        while fname.suffix:
            fname = pathlib.Path(fname.stem)
        cdns = next(fpath.cdns_dir_path.glob(fname.name + cdns_file_pattern))
        if cdns:
            if verbose:
                print('Add {} to cdns-to-tsv'.format(cdns))
            if dryrun:
                res += 1
            else:
                pendingpath = dp.DSVPath(cdns).incoming_pending_file_path
                # Might have multiple TSV for same C-DNS. If conversion
                # already pending, do nothing but remove the TSV.
                if pendingpath.exists():
                    logging.debug('C-DNS {} for {} already queued for conversion'.format(cdns, f))
                    res += 1
                    fpath.path.unlink()
                elif link(cdns, pendingpath):
                    writer.add('cdns-to-tsv', pendingpath)
                    res += 1
                    fpath.path.unlink()
        else:
            logging.error('C-DNS file for {} missing, TSV cannot be recreated.'.format(f))
            if verbose:
                print('C-DNS file for {} missing, TSV cannot be recreated.'.format(f))

    return res

def process_pending(writer, path,
                    cdns_file_pattern, tsv_file_pattern, verbose, dryrun):
    """Refill queue from pending directories. Return count."""
    res = 0
    for f in files_to_process(path, INCOMING_DIR_PATTERN + '/' + dp.PENDING_DIR, cdns_file_pattern):
        if verbose:
            print('Add {} to cdns-to-tsv'.format(f))
        if not dryrun:
            writer.add('cdns-to-tsv', f)
        res += 1

    for f in files_to_process(path, CDNS_DIR_PATTERN + '/' + dp.PENDING_DIR, cdns_file_pattern):
        if verbose:
            print('Add {} to cdns-to-tsv'.format(f))
        if not dryrun:
            writer.add('cdns-to-tsv', f, dq.JobPrecedence.low)
        res += 1

    for f in files_to_process(path, INCOMING_DIR_PATTERN + '/' + dp.PENDING_DIR, tsv_file_pattern):
        if verbose:
            print('Add {} to import-tsv'.format(f))
        if not dryrun:
            writer.add('import-tsv', f)
        res += 1

    for f in files_to_process(path, CDNS_DIR_PATTERN + '/' + dp.PENDING_DIR, tsv_file_pattern):
        if verbose:
            print('Add {} to import-tsv'.format(f))
        if not dryrun:
            writer.add('import-tsv', f)
        res += 1

    for f in files_to_process(path, PCAP_DIR_PATTERN + '/' + dp.PENDING_DIR, cdns_file_pattern):
        if verbose:
            print('Add {} to cdns-to-pcap'.format(f))
        if not dryrun:
            writer.add('cdns-to-pcap', f, dq.JobPrecedence.low)
        res += 1
    return res

def add_args(parser):
    parser.add_argument('-s', '--source',
                        dest='source', action='store',
                        choices=['incoming', 'cbor', 'pcap', 'pending',
                                 'error', 'regen-error-tsv'],
                        required=True,
                        help='incoming, cbor, pcap, pending or error',
                        metavar='SOURCES')
    parser.add_argument('--from',
                        dest='from_date', action='store',
                        type=dd.arg_valid_date_type,
                        default=None,
                        help='don\'t process cbor data from before this date',
                        metavar='DATE')
    parser.add_argument('--to',
                        dest='to_date', action='store',
                        type=dd.arg_valid_date_type,
                        default=None,
                        help='don\'t process cbor data from at or after this date',
                        metavar='DATE')
    parser.add_argument('-v', '--verbose',
                        action='store_true', default=False,
                        help='enable verbosity')
    parser.add_argument('-n', '--dry-run',
                        dest='dryrun', action='store_true', default=False,
                        help='perform a trial run')

def main(args, cfg):
    if args.from_date and args.to_date and (args.from_date >= args.to_date):
        print('Error: To date must be after From date', file=sys.stderr)
        return 1

    try:
        datastore_cfg = cfg['datastore']

        try:
            lock = dl.DSVLock(datastore_cfg['user'], datastore_cfg['lockfile'].format('import'))
            lock.lock()
        except PermissionError:
            logging.error('Import is frozen.')
            print('Import is frozen.', file=sys.stderr)
            return 1
        except BlockingIOError:
            logging.error('Another import is active.')
            print('Another import is active.', file=sys.stderr)
            return 1
        except dl.WrongUserException as e:
            logging.error(str(e))
            print(str(e), file=sys.stderr)
            return 1

        server_filters[None] = Filter(pathlib.Path(datastore_cfg['path']))

        qcontext = dq.QueueContext(cfg, sys.argv[0])
        with qcontext.writer() as writer:
            if args.source == 'incoming':
                n = process_incoming(writer,
                                     datastore_cfg['path'],
                                     datastore_cfg['cdns_file_pattern'],
                                     args.verbose, args.dryrun)
            elif args.source == 'cbor':
                n = process_cbor(writer,
                                 datastore_cfg['path'],
                                 datastore_cfg['cdns_file_pattern'],
                                 args.from_date, args.to_date,
                                 args.verbose, args.dryrun)
            elif args.source == 'pcap':
                n = process_pcap(writer,
                                 datastore_cfg['path'],
                                 datastore_cfg['cdns_file_pattern'],
                                 args.from_date, args.to_date,
                                 args.verbose, args.dryrun)
            elif args.source == 'error':
                n = process_error(writer,
                                  datastore_cfg['path'],
                                  datastore_cfg['cdns_file_pattern'],
                                  datastore_cfg['tsv_file_pattern'],
                                  args.verbose, args.dryrun)
            elif args.source == 'regen-error-tsv':
                n = process_regen_tsv(writer,
                                      datastore_cfg['path'],
                                      datastore_cfg['cdns_file_pattern'],
                                      datastore_cfg['tsv_file_pattern'],
                                      args.verbose, args.dryrun)
            else:
                n = process_pending(writer,
                                    datastore_cfg['path'],
                                    datastore_cfg['cdns_file_pattern'],
                                    datastore_cfg['tsv_file_pattern'],
                                    args.verbose, args.dryrun)

        logging.info('Import/{job} complete, {njobs} jobs queued'.format(job=args.source, njobs=n))

        qstat = ""
        for q in qcontext.status():
            if len(qstat) > 0:
                qstat += ', '
            qstat += '{name}:{length}/{running}/{workers}'.format(
                name=q[0], length=q[1], running=q[2], workers=q[3])
        logging.info(qstat)
        return 0
    except ValueError as valerr:
        logging.error(valerr)
        print(valerr, file=sys.stderr)
        return 1
