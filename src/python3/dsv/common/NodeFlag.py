# Copyright 2020, 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import enum

class NodeFlag(enum.Enum):
    NONE            = 0               # No flags set

    # Flags set on nodes update.
    HIDDEN          = 0b0000000000001 # Not visible on Grafana
    HIDDEN_TEST     = 0b0000000000010 # Not visible on test Grafana
    INACTIVE        = 0b0000000000100 # Not present in nodes.csv
    NO_SERVICE_ADDR = 0b0000000001000 # No service address

    # Derived flag combinations.
    NOT_RSSAC       = 0b0000000001100 # Inactive or no service address
