# Copyright 2018-2020 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import datetime
import enum
import logging
import threading
import time

import gear

class JobPrecedence(enum.Enum):
    high = gear.PRECEDENCE_HIGH
    normal = gear.PRECEDENCE_NORMAL
    low = gear.PRECEDENCE_LOW

class QueueJob:
    def __init__(self, job):
        self._job = job

    @property
    def queue(self):
        return self._job.name.decode()

    @property
    def arg(self):
        params = self._job.arguments.decode().split('|')
        try:
            retry_count = int(params[-1])
        except (IndexError, ValueError):
            retry_count = 0
        notbefore = None
        if len(params) > 2:
            try:
                notbefore = datetime.datetime.fromtimestamp(float(params[1]))
            except (IndexError, ValueError, OverflowError):
                pass
        return (params[0], notbefore, retry_count)

    def failed(self):
        self._job.sendWorkFail()

    def done(self):
        self._job.sendWorkComplete()

class QueueReader:
    def __init__(self, client_id, host, port):
        self._client = gear.Worker(client_id)
        self._host = host
        self._port = port
        self._stop_thread = None
        self._stop_thread_running = False

    def __enter__(self):
        self._client.addServer(self._host, self._port)
        self._client.waitForServer()
        self._stop_thread_running = True
        self._stop_thread = threading.Thread(target=self.stop_waiting_for_jobs,
                                             name='QueueReaderStopWaiting')
        self._stop_thread.daemon = True
        self._stop_thread.start()
        return self

    def __exit__(self, *args):
        self._stop_thread_running = False
        self._stop_thread.join()
        self._client.shutdown()

    def register(self, queue):
        self._client.registerFunction(queue)

    def unregister(self, queue):
        self._client.unRegisterFunction(queue)

    def register_clear(self):
        self._client.setFunctions([])

    def get(self):
        try:
            job = QueueJob(self._client.getJob())
            logging.debug('Got {arg} from {queue}'.format(queue=job.queue, arg=job.arg))
            return job
        except gear.InterruptedError:
            return None

    def stop_waiting_for_jobs(self):
        while self._stop_thread_running:
            time.sleep(1)
            self._client.stopWaitingForJobs()

class QueueWriter:
    def __init__(self, client_id, host, port):
        self._client = gear.Client(client_id)
        self._host = host
        self._port = port

    def __enter__(self):
        self._client.addServer(self._host, self._port)
        self._client.waitForServer()
        return self

    def __exit__(self, *args):
        self._client.shutdown()

    def add(self, queue, arg, precedence=JobPrecedence.normal, notbefore=None, retry_count=0):
        logging.debug('Add {arg} to {queue}{precedence}{notbefore}'.format(
            queue=queue, arg=arg,
            precedence=' ({} precedence)'.format(precedence.name) \
            if precedence != JobPrecedence.normal else '',
            notbefore=' (not before {})'.format(notbefore) if notbefore else ''))
        sarg = str(arg)
        sarg += '|{notb4}|{retry_count}'.format(
            notb4=notbefore.timestamp() if notbefore else '',
            retry_count=retry_count)
        self._client.submitJob(gear.Job(queue, sarg.encode()),
                               background=True,
                               precedence=precedence.value)

    def status(self):
        req = gear.StatusAdminRequest()
        self._client.getConnection().sendAdminRequest(req)
        res = []
        for line in req.response.decode().split('\n'):
            if line == '.':
                break
            queue, jobs, running, workers = line.split('\t')
            res.append((queue, int(jobs), int(running), int(workers)))
        return res

    def version(self):
        req = gear.VersionAdminRequest()
        self._client.getConnection().sendAdminRequest(req)
        return req.response.decode()

class QueueContext:
    def __init__(self, config, client_id):
        gearman_cfg = config['gearman']
        self._host = gearman_cfg['host']
        self._port = gearman_cfg['port']
        self._client_id = client_id

    def reader(self):
        return QueueReader(self._client_id, self._host, self._port)

    def writer(self):
        return QueueWriter(self._client_id, self._host, self._port)

    def status(self):
        with self.writer() as writer:
            return writer.status()

    def version(self):
        with self.writer() as writer:
            return writer.version()
