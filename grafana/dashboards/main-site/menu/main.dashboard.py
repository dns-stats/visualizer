# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Visualizer main dashboard

import textwrap

import grafanalib.core as GCore

import grafanacommon as GCommon

dashboard = GCommon.Dashboard(
    title = "DNS-STATS Visualizer main menu",
    timePicker = GCommon.TimePicker(
        refreshIntervals = GCore.DEFAULT_TIME_PICKER.refreshIntervals,
        timeOptions = GCore.DEFAULT_TIME_PICKER.timeOptions,
        nowDelay = '1h',
        hidden=True),
    uid = "dsv-main",
    rows = [
        GCore.Row(
            height = GCore.Pixels(330),
            panels = [
                GCommon.HTMLPanel('grafana/dashboards/main-site/menu/menu-timelines.html', 'Timelines'),
            ],
        ),
        GCore.Row(
            height = GCore.Pixels(360),
            panels = [
                GCommon.HTMLPanel('grafana/dashboards/main-site/menu/menu-other.html', 'Other metrics'),
            ],
        ),
        GCommon.FOOTER_ROW,
    ],
).auto_panel_ids()
