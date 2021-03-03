# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Aggregation client subnet statistics

import textwrap

import grafanalib.core as GCore

import grafanacommon as GCommon

def network_query_node(agginfo, nodesel):
    return GCore.Row(
        panels = [
            GCore.Table(
                span = 12,
                dataSource = 'Visualizer',
                title = 'Top node clients by subnet',
                showHeader = True,
                styles = [
                    GCore.ColumnStyle(
                        pattern = 'Prefix',
                        alias = 'AS Subnet',
                        ),
                    GCore.ColumnStyle(
                        pattern = 'QPS',
                        alias = 'Avg. QPS',
                        type = GCore.NumberColumnStyleType(
                        )
                        ),
                ],
                targets = [
                    GCommon.ClickHouseTarget(
                        database = agginfo['database'],
                        table = 'BGPPrefix' + agginfo['table_suffix'],
                        format = GCore.TABLE_TARGET_FORMAT,
                        round = agginfo['round'],
                        query = textwrap.dedent("""\
                          SELECT Prefix, QPS, name AS Name
                          FROM
                          (
                            SELECT
                            Prefix,
                            sum(toUInt64(Count)) / ($to - $from) AS QPS,
                            NodeID
                            FROM $table
                            WHERE $timeFilter AND NodeID IN {nodesel}
                            GROUP BY Prefix, NodeID
                            ORDER BY QPS DESC
                            LIMIT 25
                          )
                          ALL INNER JOIN
                            {nodeinfo_database}.node_text
                            ON NodeID=node_id""".format(
                                nodesel=nodesel,
                                nodeinfo_database=agginfo['nodeinfo_database'])),
                        refId = 'A'
                    )
                ]
            ),
        ]
    )

def dash(myuid, agginfo, nodesel, **kwargs):
    return GCommon.Dashboard(
        title = "Client subnet statistics",
        tags = [
            agginfo['graph_tag']
        ],
        uid = myuid,
        rows = [
            GCore.Row(
                height = GCore.Pixels(50),
                panels = [
                    GCommon.HTMLPanel('grafana/common/dashboards/aggregated/client_subnet_statistics_header.html', transparent=True),
                    ],
            ),
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'Busiest client ASNs',
                        layout = GCommon.BarChartLayout(
                            xaxis = GCommon.BarChartAxis(
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_CATEGORY,
                                tickangle = -45,
                                tickmargin = 55,
                            ),
                            yaxis = GCommon.BarChartAxis(
                                title = 'Queries per second',
                            ),
                        ),
                        traces = [
                            GCommon.BarChartTrace(
                                name = 'nASN',
                                color = '#33B5E5',
                                x = 'ASN',
                                y = 'ASNCnt',
                                text = 'ASNCnt',
                            ),
                        ],
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'AsnQtype' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    ClientASN AS ASN,
                                    sum(Cnt) / ($to - $from) AS ASNCnt
                                  FROM
                                  (
                                    SELECT
                                      ClientASN,
                                      sum(Count) AS Cnt
                                    FROM $table
                                    WHERE
                                      $timeFilter
                                    AND NodeID IN {nodesel}
                                    GROUP BY ClientASN
                                    ORDER BY Cnt DESC
                                    LIMIT 20
                                  )
                                  GROUP BY ClientASN
                                  ORDER BY ASNCnt DESC, ClientASN""".format(
                                      nodesel=nodesel)),
                                refId = 'A'
                            )
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'DNSKEY Queries by ASN',
                        layout = GCommon.BarChartLayout(
                            xaxis = GCommon.BarChartAxis(
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_CATEGORY,
                                tickangle = -45,
                                tickmargin = 55,
                            ),
                            yaxis = GCommon.BarChartAxis(
                                title = 'Queries per second',
                            ),
                        ),
                        traces = [
                            GCommon.BarChartTrace(
                                name = 'nASN',
                                color = '#33B5E5',
                                x = 'ASN',
                                y = 'ASNCnt',
                                text = 'ASNCnt',
                            ),
                        ],
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'AsnQtype' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    ClientASN AS ASN,
                                    sum(Cnt) / ($to - $from) AS ASNCnt
                                  FROM
                                  (
                                    SELECT
                                      ClientASN,
                                      sum(Count) AS Cnt
                                    FROM $table
                                    WHERE
                                      $timeFilter
                                    AND NodeID IN {nodesel}
                                    AND QueryType = 48
                                    GROUP BY ClientASN
                                    ORDER BY Cnt DESC
                                    LIMIT 30
                                  )
                                  GROUP BY ClientASN
                                  ORDER BY ASNCnt DESC, ClientASN""".format(
                                      nodesel=nodesel)),
                                refId = 'A'
                            )
                        ],
                    ),
                ],
            ),
            GCore.Row(
                height = GCore.Pixels(GCore.DEFAULT_ROW_HEIGHT.num * 2),
                panels = [
                    GCommon.BarChart(
                        title = 'Clients by subnet',
                        orientation = GCommon.BAR_CHART_ORIENTATION_HORIZONTAL,
                        layout = GCommon.BarChartLayout(
                            xaxis = GCommon.BarChartAxis(
                                title = 'Queries per second',
                            ),
                            yaxis = GCommon.BarChartAxis(
                                autotick = False,
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_CATEGORY,
                                tickmargin = 110,
                                title = 'AS Subnet',
                            ),
                        ),
                        traces = [
                            GCommon.BarChartTrace(
                                name = 'Subnet',
                                color = '#A352CC',
                                x = 'QPS',
                                y = 'Subnet',
                                text = 'QPS',
                            ),
                        ],
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'BGPPrefix' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      Subnet,
                                      QPS
                                  FROM
                                  (
                                      SELECT
                                          Prefix AS Subnet,
                                          sum(Count)/($to - $from) AS QPS
                                      FROM $table
                                      WHERE $timeFilter
                                          AND NodeID IN {nodesel}
                                      GROUP BY Prefix
                                      ORDER BY QPS DESC
                                      LIMIT 30
                                  )
                                  ORDER BY QPS ASC""".format(
                                      nodesel=nodesel)),
                                refId = 'A'
                            )
                        ],
                    ),
                ],
            ),
        ]
    )
