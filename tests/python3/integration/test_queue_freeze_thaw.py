# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import importlib
import pathlib

import common

dqf = importlib.import_module('dsv.commands.queue_freeze')
dqt = importlib.import_module('dsv.commands.queue_thaw')

class TestRun(common.DSVTestCase):
    def test_freeze(self):
        queues = self._config['datastore']['queues'].split(',')
        for q in queues:
            args = common.get_args(dqf, [q])
            self.assertEqual(dqf.main(args, self._config), 0)
            self.assertNotEqual(dqf.main(args, self._config), 0)
            lockpath = self._config['datastore']['lockfile'].format(q)
            lockfile = pathlib.Path(lockpath)
            self.assertTrue(lockfile.is_file())
            fmode = lockfile.stat().st_mode
            self.assertEqual(fmode & 0o200, 0)
            self.assertEqual(dqt.main(args, self._config), 0)
            self.assertTrue(lockfile.is_file())
            fmode = lockfile.stat().st_mode
            self.assertNotEqual(fmode & 0o200, 0)
            self.assertNotEqual(dqt.main(args, self._config), 0)

    def test_bad_freeze(self):
        queues = ['plugh', 'xyzzy']
        for q in queues:
            args = common.get_args(dqf, [q])
            self.assertNotEqual(dqf.main(args, self._config), 0)
            self.assertNotEqual(dqt.main(args, self._config), 0)
