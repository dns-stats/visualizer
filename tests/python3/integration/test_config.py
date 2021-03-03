# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import importlib

import common

dc = importlib.import_module('dsv.commands.config')

class TestRun(common.DSVTestCase):
    def test_config(self):
        args = common.get_args(dc, ['datastore', 'queues'])
        self.assertEqual(dc.main(args, self._config), 0)
        self._stdout.seek(0)
        output = self._stdout.readlines()
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], 'cdns-to-pcap,cdns-to-tsv,import-tsv\n')

    def test_bad_config(self):
        args = common.get_args(dc, ['plugh', 'xyzzy'])
        self.assertNotEqual(dc.main(args, self._config), 0)

    def test_random_config(self):
        args = common.get_args(dc, ['-r', 'datastore', 'queues'])
        self.assertEqual(dc.main(args, self._config), 0)
        self._stdout.seek(0)
        output = self._stdout.readlines()
        self.assertEqual(len(output), 1)
        self.assertIn(output[0].strip(), ['cdns-to-pcap', 'cdns-to-tsv', 'import-tsv'])
