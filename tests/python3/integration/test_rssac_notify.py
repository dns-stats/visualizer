# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import importlib

import common
import dsv.common.Queue as dq

drn = importlib.import_module('dsv.commands.rssac_notify')

class TestRun(common.DSVTestCase):
    def test_cmp_serial(self):
        self.assertEqual(0, drn.cmp_serial(2019090101, 2019090101))
        self.assertEqual(-1, drn.cmp_serial(2019090101, 2019090102))
        self.assertEqual(1, drn.cmp_serial(2019090102, 2019090101))

        self.assertEqual(-1, drn.cmp_serial(1, 0x7FFFFFFF))
        self.assertEqual(1, drn.cmp_serial(1, 0x80000000))

        self.assertEqual(-1, drn.cmp_serial(2, 0x80000000))
        self.assertEqual(1, drn.cmp_serial(2, 0x80000001))

    def test_find_latest_serial(self):
        self.assertEqual(None, drn.find_latest_serial([]))
        self.assertEqual(2019090101, drn.find_latest_serial([
            2019090101,
        ]))
        self.assertEqual(2019090101, drn.find_latest_serial([
            2019083101,
            2019090101,
        ]))
        self.assertEqual(2019090103, drn.find_latest_serial([
            2019083101,
            2019090101,
            2019090103,
            2019083102,
        ]))

    def test_get6addr(self):
        self.assertFalse(drn.get6addr('ipv6.google.com')[0].startswith('::ffff:'))
        self.assertTrue(drn.get6addr('ipv4.google.com')[0].startswith('::ffff:'))
