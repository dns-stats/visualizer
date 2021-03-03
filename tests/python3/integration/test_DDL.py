# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import argparse
import datetime
import pathlib
import unittest

import dsv.common.DDL as DDL

import common

class TestDDLActions(DDL.DDLActions):
    def __init__(self):
        self.actions = []

    def apply_ddl(self, ddl_file, version, action=DDL.ACTION_APPLY):
        self.actions.append('{}|{}|{}|'.format(ddl_file.stem, version, 'apply' if action == DDL.ACTION_APPLY else 'rollback'))

    def read_ddl_info(self, ddl_path):
        return [
            (1, datetime.datetime(2021, 1, 19, 10, 0, 0), DDL.ACTION_APPLY),
            (1, datetime.datetime(2021, 1, 19, 10, 5, 0), DDL.ACTION_ROLLBACK),
            (1, datetime.datetime(2021, 1, 19, 10, 10, 0), DDL.ACTION_APPLY),
        ]

def get_args(argv=[]):
    parser = argparse.ArgumentParser('DDL')
    DDL.add_args(parser)
    return parser.parse_args(argv)

class TestRun(common.DSVTestCase):
    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.ddl_toapply_path = pathlib.Path('tests/python3/integration/ddl-toapply')
        self.ddl_applied_path = pathlib.Path('tests/python3/integration/ddl-applied')

    def test_ddl_files_toapply(self):
        files = DDL.ddl_files(self.ddl_toapply_path)
        self.assertEqual(len(files), 2)
        self.assertEqual(int(files[0].stem), 1)
        self.assertEqual(int(files[1].stem), 2)

    def test_ddl_files_applied(self):
        files = DDL.ddl_files(self.ddl_applied_path)
        self.assertEqual(len(files), 1)
        self.assertEqual(int(files[0].stem), 1)

    def test_ddl_rollback_files(self):
        files = DDL.ddl_rollback_files(self.ddl_toapply_path, 1)
        self.assertEqual(len(files), 1)
        files = DDL.ddl_rollback_files(self.ddl_toapply_path, 2)
        self.assertEqual(len(files), 0)

    def test_active_ddls(self):
        actions = TestDDLActions()
        active = DDL.active_ddls(actions.read_ddl_info(self.ddl_toapply_path))
        self.assertEqual(len(active), 1)
        self.assertEqual(active[1], datetime.datetime(2021, 1, 19, 10, 10, 00))

    def test_apply_toapply(self):
        actions = TestDDLActions()
        args = get_args(['--quiet', '--action', 'update', str(self.ddl_toapply_path)])
        res = DDL.main(args, actions)
        self.assertEqual(res, 0)
        self.assertEqual(len(actions.actions), 1)
        self.assertEqual(actions.actions[0], '0002|2|apply|')

    def test_apply_applied(self):
        actions = TestDDLActions()
        args = get_args(['--quiet', '--action', 'update', str(self.ddl_applied_path)])
        res = DDL.main(args, actions)
        self.assertEqual(res, 0)
        self.assertEqual(len(actions.actions), 0)

    def test_rollback_toapply(self):
        actions = TestDDLActions()
        args = get_args(['--quiet', '--action', 'rollback', str(self.ddl_toapply_path)])
        res = DDL.main(args, actions)
        self.assertEqual(res, 0)
        self.assertEqual(len(actions.actions), 1)
        self.assertEqual(actions.actions[0], '0001-rollback|1|rollback|')

    def test_rollback_applied(self):
        actions = TestDDLActions()
        args = get_args(['--quiet', '--action', 'rollback', str(self.ddl_applied_path)])
        res = DDL.main(args, actions)
        self.assertEqual(res, 1)
        self.assertEqual(len(actions.actions), 0)

    def test_status_toapply(self):
        actions = TestDDLActions()
        args = get_args(['--quiet', '--action', 'status', str(self.ddl_toapply_path)])
        res = DDL.main(args, actions)
        self.assertEqual(res, 1)

    def test_status_applied(self):
        actions = TestDDLActions()
        args = get_args(['--quiet', '--action', 'status', str(self.ddl_applied_path)])
        res = DDL.main(args, actions)
        self.assertEqual(res, 0)

    def test_exception_raised(self):
        actions = DDL.DDLActions()
        args = get_args(['--quiet', '--action', 'status', str(self.ddl_applied_path)])
        res = DDL.main(args, actions)
        self.assertEqual(res, 2)
