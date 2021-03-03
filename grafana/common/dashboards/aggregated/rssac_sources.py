# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Aggregation RSSAC plots

import textwrap

import grafanalib.core as GCore

import grafanacommon as GCommon

def dash(myuid, agginfo, nodesel, **kwargs):
    return GCommon.Dashboard(
        title = "RSSAC sources",
        tags = [
            agginfo['graph_tag']
        ],
        uid = myuid,
        rows = [
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'Unique source addresses',
                        orientation = GCommon.BAR_CHART_ORIENTATION_HORIZONTAL,
                        layout = GCommon.BarChartLayout(
                            xaxis = GCommon.BarChartAxis(
                                title = 'Number of unique sources',
                            ),
                            yaxis = GCommon.BarChartAxis(
                                tickmargin = 55,
                                title = 'IP Version/Aggregation',
                            ),
                        ),
                        traces = [
                            GCommon.BarChartTrace(
                                name = 'IPv6/64',
                                color = '#33B5E5',
                                x = 'IPv664Cnt',
                                y = 'IPv664Proto',
                                text = 'IPv664Cnt',
                            ),
                            GCommon.BarChartTrace(
                                name = 'IPv6',
                                color = '#1F60C4',
                                x = 'IPv6Cnt',
                                y = 'IPv6Proto',
                                text = 'IPv6Cnt',
                            ),
                            GCommon.BarChartTrace(
                                name = 'IPv4',
                                color = '#8877D9',
                                x = 'IPv4Cnt',
                                y = 'IPv4Proto',
                                text = 'IPv4Cnt',
                            ),
                        ],
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'UniqueIPv6Addr' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      'IPv6/64' AS IPv664Proto,
                                      uniqMerge(IPv664Addr) AS IPv664Cnt
                                  FROM $table
                                  WHERE $timeFilter
                                  AND NodeID IN {nodesel}""".format(
                                      nodesel=nodesel)),
                                refId = 'A'
                            ),
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'UniqueIPv6Addr' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      'IPv6' AS IPv6Proto,
                                      uniqMerge(IPv6Addr) AS IPv6Cnt
                                  FROM $table
                                  WHERE $timeFilter
                                  AND NodeID IN {nodesel}""".format(
                                      nodesel=nodesel)),
                                refId = 'B'
                            ),
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'UniqueIPv4Addr' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      'IPv4' AS IPv4Proto,
                                      uniqMerge(IPv4Addr) AS IPv4Cnt
                                  FROM $table
                                  WHERE $timeFilter
                                  AND NodeID IN {nodesel}""".format(
                                      nodesel=nodesel)),
                                refId = 'C'
                            ),
                        ],
                    ),
                ],
            ),
        ]
    )
