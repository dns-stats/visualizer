# Copyright 2018-2019 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import argparse
import datetime

DATE_TIME_FORMATS = ['%Y-%m-%d %H:%M:%S', '%Y%m%d_%H%M%S', '%Y-%m-%d']

def parse_datetime(arg):
    for dtf in DATE_TIME_FORMATS:
        try:
            return datetime.datetime.strptime(arg, dtf)
        except ValueError:
            pass
    raise ValueError('{0} is not a valid date'.format(arg))

def arg_valid_date_type(arg):
    try:
        return parse_datetime(arg)
    except ValueError:
        raise argparse.ArgumentTypeError(
            'Date {0} not valid. Expected format YYYY-MM-DD or YYYY-MM-DD HH:MM:SS.'.format(arg))
