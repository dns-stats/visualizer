# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import importlib

import common

dcsi = importlib.import_module('dsv.commands.clickhouse_sys_info')

class TestRun(common.DSVTestCase):
    def test_all_used(self):
        print('disc-block-size\ndisc-size\ndisc-available\ndisc-percent-free\ndisc-percent-used', file=self._stdin)
        self._stdin.seek(0)
        args = common.get_args(dcsi)
        self.assertEqual(dcsi.main(args, self._config), 0)

        self._stdout.seek(0)
        output = self._stdout.readlines()
        out_split = [o.split('\t') for o in output]
        for o in out_split:
            d = int(o[1])
            self.assertTrue(d >= 0)
            if o[0].find('percent') != -1:
                self.assertTrue(d <= 100)
        self.assertEqual(out_split[0][0], 'disc-block-size')
        self.assertEqual(out_split[1][0], 'disc-size')
        self.assertEqual(out_split[2][0], 'disc-available')
        self.assertEqual(out_split[3][0], 'disc-percent-free')
        self.assertEqual(out_split[4][0], 'disc-percent-used')

    def test_unused(self):
        print('xyzzy', file=self._stdin)
        self._stdin.seek(0)
        args = common.get_args(dcsi)
        self.assertEqual(dcsi.main(args, self._config), 1)
