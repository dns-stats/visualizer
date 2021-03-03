# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import importlib

import common

dl = importlib.import_module('dsv.commands.log')

class TestRun(common.DSVTestCase):
    def test_log(self):
        args = common.get_args(dl, ['-l', 'critical', 'log message'])
        self.assertEqual(dl.main(args, self._config), 0)
        self._log.seek(0)
        output = self._log.readlines()
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], 'root:CRITICAL:log message\n')
