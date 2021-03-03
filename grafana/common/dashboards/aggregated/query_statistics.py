# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Aggregation query statistics

import textwrap

import grafanalib.core as GCore

import querystatsgraph as qsg
import grafanacommon as GCommon

def dash(myuid, agginfo, nodesel, **kwargs):
    return GCommon.Dashboard(
        title = 'Query statistics',
        tags = [
            agginfo['graph_tag']
        ],
        uid = myuid,
        rows = [
            GCore.Row(
                panels = [
                    GCommon.QPSGraph(
                        title = 'Queries',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Queries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                    SELECT
                                      $timeSeries AS t,
                                      sum(QueryCount)/{interval_divisor} AS QPS
                                    FROM $table
                                    WHERE
                                      $timeFilter
                                    AND NodeID IN {nodesel}
                                    GROUP BY t
                                    ORDER BY t""".format(
                                        interval_divisor=agginfo['interval_divisor'],
                                        nodesel=nodesel)),
                                refId = 'A'
                            )
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.QPSGraph(
                        title = 'Queries by region',
                        targets = [ qsg.QPSTargetGroup(agginfo, 'region_name', nodesel) ],
                    ),
                    GCommon.QPSGraph(
                        title = 'Queries by country',
                        targets = [ qsg.QPSTargetGroup(agginfo, 'country_name', nodesel) ],
                    ),
                ]
            ),
        ]
    )
