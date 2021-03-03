# Copyright 2018-2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import configparser
import logging.config
import os.path
import sys

_defaults = {
    'gearman': {
        'host': 'localhost',
        'port': 4730
    },
    'datastore': {
        'path': '/var/lib/dns-stats-visualizer/cdns/',
        'cdns_file_pattern': '*.cdns.xz',
        'tsv_file_pattern': '*.tsv',
        'lockfile': '/run/lock/dns-stats-visualizer/{}.lock',
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
        'host': '',
        'default_ddl_path': '/usr/share/dns-stats-visualizer/sql/postgres/ddl',
    },
    'clickhouse': {
        'servers': 'dsv-clickhouse',
        'dbdir': '/var/lib/clickhouse',
        'import-server': 'dsv-clickhouse',
        'database': 'dsv',
        'user': 'dsv',
        'password': 'dsv',
        'querytable': 'QueryResponse',
        'packetcountstable': 'PacketCounts',
        'default_ddl_path': '/usr/share/dns-stats-visualizer/sql/clickhouse/ddl',
        'dataset-name-raw': 'Raw data',
        'dataset-database-raw': 'dsv',
        'dataset-table-pattern-raw': 'QueryResponseShard',
        'dataset-name-5min': '5 minute aggregation',
        'dataset-database-5min': 'dsv_five_minute',
        'dataset-table-pattern-5min': '.*Shard',
        'dataset-extra-tables-5min': 'dsv.AAATopUndelegatedTldPerFiveMinsShard,dsv.PacketCountsShard,dsv.ZoneLatencyShard',
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
        'xfr-server': '',
        'load-time-threshold': 95
    },
    'geo': {
        'url': 'https://download.maxmind.com/app/geoip_download'
               '?edition_id=GeoLite2-City-CSV&license_key={licencekey}&'
               'suffix=zip',
        'licencekey': 'XXXXXXXXXXXX',
    },
    'loggers': {
        'keys': 'root'
    },
    'logger_root': {
        'level': 'INFO',
        'handlers': 'syslog'
    },
    'handlers': {
        'keys': 'stream,syslog,null'
    },
    'handler_null': {
        'class': 'NullHandler',
        'formatter': 'default',
        'level': 'NOTSET',
        'args': '()'
    },
    'handler_stream': {
        'class': 'StreamHandler',
        'formatter': 'default',
        'level': 'NOTSET',
        'args': '(sys.stdout,)'
    },
    'handler_syslog': {
        'class': 'handlers.SysLogHandler',
        'formatter': 'syslog',
        'level': 'NOTSET',
        'args': '("/dev/log",)'
    },
    'formatters': {
        'keys': 'default,syslog'
    },
    'formatter_default': {
        'format': '%(asctime)s: %(name)s - %(levelname)s - %(message)s'
    },
    'formatter_syslog': {
        'format': 'APPNAME - %(name)s - %(levelname)s - %(message)s'
    },
    'urls': {
        'tldlist': 'https://data.iana.org/TLD/tlds-alpha-by-domain.txt',
        'tldpage': 'https://www.iana.org/domains/root/db/{}.html'
    }
}

class Config(configparser.ConfigParser):
    def __init__(self, configfile=None):
        super().__init__()
        self.read_dict(_defaults)
        if configfile:
            with open(configfile) as f:
                self.read_file(f)
        else:
            self.read([
                '/etc/dns-stats-visualizer/dsv.cfg',
                '/etc/dns-stats-visualizer/private.cfg',
                os.path.expanduser('~/.dsv.cfg'),
                os.path.expanduser('~/.dsv.private.cfg'),
            ])

        app_name = os.path.basename(sys.argv[0])
        for f in self['formatters']['keys'].split(','):
            f_key = 'formatter_' + f
            val = self.get(f_key, 'format', raw=True)
            self.set(f_key, 'format', val.replace('APPNAME', app_name))

        logging.config.fileConfig(self)
