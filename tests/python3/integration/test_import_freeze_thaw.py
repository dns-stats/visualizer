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

dif = importlib.import_module('dsv.commands.import_freeze')
dit = importlib.import_module('dsv.commands.import_thaw')
di = importlib.import_module('dsv.commands.import')

class TestRun(common.DSVTestCase):
    def test_freeze(self):
        args = common.get_args(dif)
        self.assertEqual(dif.main(args, self._config), 0)
        self.assertNotEqual(dif.main(args, self._config), 0)
        lockpath = self._config['datastore']['lockfile'].format('import')
        lockfile = pathlib.Path(lockpath)
        self.assertTrue(lockfile.is_file())
        fmode = lockfile.stat().st_mode
        self.assertEqual(fmode & 0o200, 0)

        di_args = common.get_args(di, ['-s', 'incoming'])
        self.assertNotEqual(di.main(di_args, self._config), 0)

        self.assertEqual(dit.main(args, self._config), 0)
        self.assertTrue(lockfile.is_file())
        fmode = lockfile.stat().st_mode
        self.assertNotEqual(fmode & 0o200, 0)
        self.assertNotEqual(dit.main(args, self._config), 0)
