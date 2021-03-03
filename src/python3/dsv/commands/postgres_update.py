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
# Keep the Postgres schema up to date. The Postgres user 'dsv' and
# database 'dsv' must have already been created using the script
# dsv-postgres-create.
#
# Usage: dsv-postgres-update <ddl-directory>
#

import logging
import textwrap

import psycopg2
import psycopg2.errorcodes

import dsv.common.DDL as dd

description = 'update Postgres schema.'

# SQL for managing the DDL management schema.
SQL_CREATE_HISTORY = textwrap.dedent("""\
    CREATE TABLE ddl_history (
      version INTEGER NOT NULL,
      applied TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
      action INTEGER NOT NULL DEFAULT 0
    )""")
SQL_UPDATE_HISTORY_FROM_V1 = textwrap.dedent("""\
    ALTER TABLE ddl_history DROP CONSTRAINT ddl_history_version_key,
                            ALTER COLUMN applied SET DEFAULT CURRENT_TIMESTAMP,
                            ADD COLUMN action INTEGER NOT NULL DEFAULT 0""")

class PostgresDDLActions(dd.DDLActions):
    def __init__(self, conn):
        self.conn = conn

    def read_ddl_info(self, ddl_path):
        query = 'SELECT version,applied,action FROM ddl_history ORDER BY applied'
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                ddl_info = cur.fetchall()
        except psycopg2.Error as err:
            if err.pgcode == psycopg2.errorcodes.UNDEFINED_COLUMN:
                self.conn.rollback()
                with self.conn.cursor() as cur:
                    cur.execute(SQL_UPDATE_HISTORY_FROM_V1)
                self.conn.commit()
                logging.info('Apply Postgres ddl_history v2 update')
                with self.conn.cursor() as cur:
                    cur.execute(query)
                    ddl_info = cur.fetchall()
            elif err.pgcode == psycopg2.errorcodes.UNDEFINED_TABLE:
                self.conn.rollback()
                with self.conn.cursor() as cur:
                    cur.execute(SQL_CREATE_HISTORY)
                self.conn.commit()
                logging.info('Create Postgres ddl_history')
                ddl_info = []
            else:
                raise err
        return ddl_info

    def apply_ddl(self, ddl_file, version, action=dd.ACTION_APPLY):
        sql = ddl_file.open().read()
        with self.conn.cursor() as cur:
            cur.execute(sql)
            cur.execute('INSERT INTO ddl_history (version, action) '
                        'VALUES (%s, %s)',
                        [version, action])
            self.conn.commit()
            logging.info('Postgres DDL: {action} {version}'.format(
                version=version, action='Rollback' if action else 'Apply'))

def add_args(parser):
    dd.add_args(parser)

def main(args, cfg):
    if not args.ddl_path:
        args.ddl_path = cfg['postgres']['default_ddl_path']

    conn = None
    try:
        pgcfg = cfg['postgres']
        conn = psycopg2.connect(host=pgcfg['host'],
                                dbname=pgcfg['database'],
                                user=pgcfg['user'],
                                password=pgcfg['password'])
        ddl_actions = PostgresDDLActions(conn)
        res = dd.main(args, ddl_actions)
        conn.close()
        return res
    except Exception:
        if conn:
            conn.rollback()
            conn.close()
        raise
