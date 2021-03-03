# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Aggregation RSSAC plots

import grafanacommon as GCommon

from dashboards.aggregated.rssac_reporting import dash

dashboard = GCommon.MakeAggDashboard(dash, 'dsv-5minagg-rssac-report', tags=[], zone_load_name_col='instance_name').auto_panel_ids()
