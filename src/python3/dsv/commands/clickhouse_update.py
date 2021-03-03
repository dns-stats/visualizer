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
# Keep the Clickhouse schema up to date. Clickhouse must be accessible
# from the configured user. 'clickhouse-client' must be installed.
#
# Usage: dsv-clickhouse-update <ddl-directory>
#

import logging
import subprocess
import textwrap

import clickhouse_driver
import clickhouse_driver.errors

import dsv.common.DDL as dd

description = 'update Clickhouse schema.'

# SQL for managing the DDL management schema. clickhouse_driver does
# not allow multiquery input, so split into individual statements.
SQL_CREATE_HISTORY = [
    'CREATE DATABASE IF NOT EXISTS dsv',
    textwrap.dedent("""\
        CREATE TABLE IF NOT EXISTS dsv.ddl_history (
          version UInt16 DEFAULT 0,
          applied DateTime DEFAULT now(),
          action UInt8 DEFAULT 0
        ) ENGINE = TinyLog"""),]
SQL_UPDATE_HISTORY_FROM_V1 = [
    textwrap.dedent("""\
        CREATE TABLE dsv.new_ddl_history (
          version UInt16 DEFAULT 0,
          applied DateTime DEFAULT now(),
          action UInt8 DEFAULT 0
        ) ENGINE = TinyLog"""),
    'INSERT INTO dsv.new_ddl_history(version, applied) ' \
        'SELECT version, applied FROM dsv.ddl_history',
    'DROP TABLE dsv.ddl_history',
    'RENAME TABLE dsv.new_ddl_history TO dsv.ddl_history',]

class ClickHouseError(Exception):
    pass

class ClickHouseDDLActions(dd.DDLActions):
    def __init__(self, ch_client):
        self.ch_client = ch_client

    def read_ddl_info(self, ddl_path):
        query = 'SELECT version,applied,action FROM dsv.ddl_history ORDER BY applied'
        try:
            ddl_info = self.ch_client.execute(query)
        except clickhouse_driver.errors.Error as err:
            if err.code == clickhouse_driver.errors.ErrorCodes.UNKNOWN_IDENTIFIER:
                for sql in SQL_UPDATE_HISTORY_FROM_V1:
                    self.ch_client.execute(sql)
                logging.info('Apply ClickHouse ddl_history v2 update')
                ddl_info = self.ch_client.execute(query)
            elif err.code == clickhouse_driver.errors.ErrorCodes.UNKNOWN_TABLE or \
                 err.code == clickhouse_driver.errors.ErrorCodes.UNKNOWN_DATABASE:
                for sql in SQL_CREATE_HISTORY:
                    self.ch_client.execute(sql)
                logging.info('Create ClickHouse ddl_history')
                ddl_info = []
            else:
                raise err
        return ddl_info

    def apply_ddl(self, ddl_file, version, action=dd.ACTION_APPLY):
        # Currently we can't do multi-queries via the driver.
        # Resort to running clickhouse-client and hope multi-query
        # is possible via the driver in future.
        ckuser = self.ch_client.connection.user
        ckpass = self.ch_client.connection.password
        ckhost = self.ch_client.connection.host
        sql = ddl_file.open().read()
        try:
            subprocess.run(['clickhouse-client', '--multiquery',
                            '--user', ckuser, '--password', ckpass,
                            '--host', ckhost],
                           input=sql,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True,
                           check=True)
            self.ch_client.execute('INSERT INTO dsv.ddl_history(version,action) VALUES',
                                   [{ 'version': version, 'action': action }])
        except FileNotFoundError as fnfe:
            raise ClickHouseError('clickhouse-client not present.') from fnfe
        except subprocess.CalledProcessError as cpe:
            raise ClickHouseError(cpe.stderr) from cpe
        logging.info('ClickHouse DDL: {action} {version}'.format(
            version=version, action='Rollback' if action else 'Apply'))

def add_args(parser):
    dd.add_args(parser)

def main(args, cfg):
    clickhouse = cfg['clickhouse']
    ch_user = clickhouse['user']
    ch_pass = clickhouse['password']

    if not args.ddl_path:
        args.ddl_path = clickhouse['default_ddl_path']

    # Host is localhost since we are expected to be running on a ClickHouse
    # machine.
    ddl_actions = ClickHouseDDLActions(clickhouse_driver.Client(
        host='localhost', user=ch_user, password=ch_pass))
    return dd.main(args, ddl_actions)
