# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import argparse
import configparser
import copy
import logging
import logging.config
import os
import pwd
import sys
import tempfile
import unittest

_testconfig = {
    'gearman': {
        'host': 'localhost',
        'port': 4730
    },
    'datastore': {
        'path': '/srv/cbor/',
        'cdns_file_pattern': '*.cbor.xz',
        'tsv_file_pattern': '*.tsv*',
        'lockfile': '/run/lock/dns-stats-visualization/{}.lock',
        'user': 'dsv',
        # NOTE: The order is important. Priority of worker processing
        # INCREASES the later in the list the queue name is.
        'queues': 'cdns-to-pcap,cdns-to-tsv,import-tsv'
    },
    'pcap': {
        'compress': 'Y',
        'compression-level': 2,
        'query-only': '',
        'pseudo-anonymise': '',
        'pseudo-anonymisation-key': '',
        'pseudo-anonymisation-passphrase': '',
        'replace': 'Y'
    },
    'postgres': {
        'connection': 'postgresql://%(user)s:%(password)s@%(host)s/%(database)s',
        'database': 'dsv',
        'user': 'dsv',
        'password': 'dsv',
        'host': 'postgres'
    },
    'clickhouse': {
        'servers': 'dsv-clickhouse1,' \
                   'dsv-clickhouse2,' \
                   'dsv-clickhouse3,' \
                   'dsv-clickhouse4,',
        'dbdir': '/src/clickhouse',
        'import-server': 'dsv1',
        'node-shard-default': 'auto',
        'database': 'dsv',
        'user': 'dsv',
        'password': 'dsv',
        'querytable': 'QueryResponse',
        'packetcountstable': 'PacketCounts',
    },
    'rssac': {
        'outdir': '.',
        'grafana-url': 'https://localhost',
        'server': 'Z-Root',
        'zone': '.',
        'tsig': {
            'name': '',
            'key': '',
            'algo': ''
            },
        'xfr-server': ''
    },
}

class DSVTestCase(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)

    def setUp(self):
        self._orig_stdin = sys.stdin
        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr
        self._stdin = tempfile.NamedTemporaryFile(mode='w+', prefix='stdin_')
        self._stdout = tempfile.NamedTemporaryFile(mode='w+', prefix='stdout_')
        self._stderr = tempfile.NamedTemporaryFile(mode='w+', prefix='stderr_')
        sys.stdin = self._stdin
        sys.stdout = self._stdout
        sys.stderr = self._stderr

        testcfg = copy.deepcopy(_testconfig)

        # Set up directories
        self._datastore_path = tempfile.TemporaryDirectory(prefix='dpath_')
        self._datastore_lockdir = tempfile.TemporaryDirectory(prefix='dlockdir_')
        self._clickhouse_dbdir = tempfile.TemporaryDirectory(prefix='cdbdir_')

        testcfg['datastore']['path'] = self._datastore_path.name
        testcfg['datastore']['lockfile'] = self._datastore_lockdir.name + '/{}.lock'
        testcfg['clickhouse']['dbdir'] = self._clickhouse_dbdir.name

        testcfg['datastore']['user'] = pwd.getpwuid(os.getuid()).pw_name

        # Set up test config object
        self._config = configparser.ConfigParser()
        self._config.read_dict(testcfg)

        self._log = tempfile.NamedTemporaryFile(mode='w+', prefix='log_')
        _log_cfg = {
            'version': 1,
            'disable_existing_loggers': True,
            'formatters': {
                'simple': {
                    'format': '%(name)s:%(levelname)s:%(message)s'
                },
            },
            'handlers': {
                'stream': {
                    'level': 'DEBUG',
                    'class': 'logging.StreamHandler',
                    'stream': self._log,
                    'formatter': 'simple'
                },
            },
            'root': {
                'handlers': ['stream'],
                'level': 'DEBUG',
                'propagate': True
            }
        }
        logging.config.dictConfig(_log_cfg)

    def tearDown(self):
        self._log.close()

        self._clickhouse_dbdir.cleanup()
        self._datastore_lockdir.cleanup()
        self._datastore_path.cleanup()

        sys.stderr = self._orig_stderr
        sys.stdout = self._orig_stdout
        sys.stdin = self._orig_stdin
        self._stderr.close()
        self._stdout.close()
        self._stdin.close()


def get_args(module, argv=[]):
    parser = argparse.ArgumentParser(module.description)
    module.add_args(parser)
    return parser.parse_args(argv)
