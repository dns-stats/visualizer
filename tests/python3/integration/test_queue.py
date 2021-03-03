# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import importlib
import pdb
import sys

from unittest.mock import patch

import common
import dsv.common.Queue as dq

cmd = importlib.import_module('dsv.commands.queue')

class TestRun(common.DSVTestCase):
    def test_queue(self):
        with patch('dsv.common.Queue.QueueWriter', autospec=True) as MockQueueWriter:
            args = common.get_args(cmd, ['-q', 'import-tsv', 'job1'])
            self.assertEqual(cmd.main(args, self._config), 0)
