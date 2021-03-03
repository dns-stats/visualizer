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
# Wait for a job to be available on a job queue. Pass it to the appropriate
# process, and check the return code.
#
# 0 = Success. Delete input file, move on to next job.
# 1 = Failure. Move input file to ..<node>/failed, move on to next job.
# 2 = Transient failure. Re-enter job in queue, sleep for delay period,
#     move on to next job.
# 3 = Success. Move on to next job, but don't attempt to delete the file.
# Any other exit code is an infrastructure exit. Log and quit.
#
# All jobs are run by executing a script named <queue-name>.sh.

import datetime
import logging
import pathlib
import subprocess
import sys
import time

import dsv.common.Lock as dl
import dsv.common.Path as dp
import dsv.common.Queue as dq

description = 'process Visualizer jobs.'

def queue_delayed_jobs(qcontext, delayed_jobs_list):
    if not delayed_jobs_list:
        return []

    now = datetime.datetime.now()
    remaining = []
    for job in delayed_jobs_list:
        queue, arg, notbefore = job
        if now >= notbefore:
            with qcontext.writer() as writer:
                writer.add(queue, arg, dq.JobPrecedence.high)
        else:
            remaining.append(job)
    return remaining

def save_delayed_jobs(qcontext, delayed_jobs_list):
    for job in delayed_jobs_list:
        queue, arg, notbefore = job
        with qcontext.writer() as writer:
            writer.add(queue, arg, dq.JobPrecedence.high, notbefore=notbefore)

def execute_job(qcontext, args, job, delayed_jobs_list):
    process = 'dsv-' + job.queue
    arg, notbefore, retry_count = job.arg
    if notbefore:
        logging.debug('From {queue} delay {arg} until {notbefore}'.format(
            queue=job.queue, arg=arg, notbefore=notbefore))
        delayed_jobs_list.append((job.queue, arg, notbefore))
        job.done()
        return

    logging.debug('From {queue} run {process} {arg} try {retry}'.format(
        queue=job.queue, process=process, arg=arg, retry=retry_count))

    t_start = time.perf_counter()
    res = subprocess.run([process, arg],
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE,
                         check=False)
    if res.returncode == 0 or res.returncode == 3:
        logging.debug('{process} {arg} OK, {runtime:0.3f}s'.format(
            process=process, arg=arg,
            runtime=(time.perf_counter() - t_start)))
        p = pathlib.Path(arg)
        if res.returncode == 0 and p.exists():
            p.unlink()
        job.done()
    elif res.returncode == 1 or (res.returncode == 2 and retry_count >= args.max_retries):
        logging.error('{process} {arg} failed, {runtime:0.3f}s'.format(
            process=process, arg=arg,
            runtime=(time.perf_counter() - t_start)))
        logging.error('Stdout: {stdout}'.format(
            stdout=res.stdout.decode().rstrip()))
        logging.error('Stderr: {stderr}'.format(
            stderr=res.stderr.decode().rstrip()))
        p = pathlib.Path(arg)
        if p.exists():
            wompath = dp.DSVPath(arg)
            errpath = wompath.error_file_path(job.queue)
            errpath.parent.mkdir(parents=True, exist_ok=True)
            wompath.path.rename(errpath)
        job.failed()
    elif res.returncode == 2:
        logging.error('{process} {arg} transient failure {count}, {runtime:0.3f}s'.format(
            process=process, arg=arg, count=retry_count,
            runtime=(time.perf_counter() - t_start)))
        logging.error('Stdout: {stdout}'.format(
            stdout=res.stdout.decode().rstrip()))
        logging.error('Stderr: {stderr}'.format(
            stderr=res.stderr.decode().rstrip()))
        job.failed()
        with qcontext.writer() as writer:
            writer.add(job.queue, arg, retry_count=retry_count + 1)
        time.sleep(args.fail_delay)
    else:
        logging.error('Infrastructure error')
        logging.error('Stdout: {stdout}'.format(
            stdout=res.stdout.decode().rstrip()))
        logging.error('Stderr: {stderr}'.format(
            stderr=res.stderr.decode().rstrip()))
        raise OSError('Infrastructure error exit code')

def add_args(parser):
    parser.add_argument('--fail-delay', '--fail_delay',
                        dest='fail_delay', action='store', type=int, default=5,
                        help='delay on process failure',
                        metavar='FAILURE_DELAY')
    parser.add_argument('--max-retries', '--max_retries',
                        dest='max_retries', action='store', type=int, default=5,
                        help='maximum times to retry a job with a transient failure',
                        metavar='RETRIES')
    parser.add_argument('--ignore-queue',
                        dest='ignore_queue', action='append',
                        help='do not process jobs on the named queue',
                        metavar='QUEUE')

def main(args, cfg):
    datastore_cfg = cfg['datastore']

    try:
        user = dl.DSVUser(datastore_cfg['user'])
        user.ensure_user()
    except dl.WrongUserException as e:
        logging.error(str(e))
        print(str(e), file=sys.stderr)
        return 1

    qcontext = dq.QueueContext(cfg, sys.argv[0])

    # Note: Order of registration is important. The last registered
    # queue is checked for jobs first. If none are on that queue, the
    # next most recently registered queue is checked, etc.
    queues = datastore_cfg['queues'].split(',')
    queue_locks = {}
    for q in queues:
        queue_locks[q] = dl.DSVLock(datastore_cfg['user'], datastore_cfg['lockfile'].format(q))
    with qcontext.reader() as reader:
        delayed_jobs_list = []
        try:
            while True:
                delayed_jobs_list = queue_delayed_jobs(qcontext, delayed_jobs_list)

                # Assess lock status.
                to_register = []
                for q in queues:
                    if (not args.ignore_queue or q not in args.ignore_queue) and \
                       not queue_locks[q].is_frozen():
                        to_register.append(q)

                if to_register:
                    reader.register_clear()
                    for q in to_register:
                        reader.register(q)
                    job = reader.get()
                    try:
                        if job:
                            execute_job(qcontext, args, job, delayed_jobs_list)
                    except OSError as ose:
                        logging.error('execution process error {err}'.format(err=ose))
                        break
                else:
                    time.sleep(1)
        except KeyboardInterrupt:
            save_delayed_jobs(qcontext, delayed_jobs_list)
            raise
