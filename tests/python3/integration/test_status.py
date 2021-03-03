# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import importlib

from unittest.mock import patch

import common
import dsv.common.Queue as dq

ws = importlib.import_module('dsv.commands.status')

class TestRun(common.DSVTestCase):
    def test_status(self):
        with patch.object(dq.QueueContext, 'status', return_value=[['queue', 'len', 'running', 'workers']]):
            args = common.get_args(ws)
            self.assertEqual(ws.main(args, self._config), 0)
        self._stdout.seek(0)
        output = self._stdout.readlines()
        self.assertEqual(len(output), 1)
        self.assertEqual(output[0], 'queue: len queued, running running, workers workers, active\n')
