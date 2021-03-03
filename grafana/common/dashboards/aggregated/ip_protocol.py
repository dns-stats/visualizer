# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Aggregation IP/Protocol

import textwrap

import grafanalib.core as GCore

import grafanacommon as GCommon

def dash(myuid, agginfo, nodesel, **kwargs):
    return GCommon.Dashboard(
        title = 'IP version and Transport',
        tags = [
            agginfo['graph_tag']
        ],
        uid = myuid,
        rows = [
            GCore.Row(
                panels = [
                    GCommon.QPSGraph(
                        title = 'Queries by IP version',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Queries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(TransportIPv6Count)/{interval_divisor} AS IPv6
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                  AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'A'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Queries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(QueryCount - TransportIPv6Count)/{interval_divisor} AS IPv4
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                  AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'B'
                            )
                        ],
                    ),
                    GCommon.QPSGraph(
                        title = 'Queries by transport version',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Queries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT t, groupArray((if(TransportTCP,'TCP','UDP'), qc))
                                  FROM
                                  (
                                    SELECT
                                      t,TransportTCP,cnt/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        TransportTCPMap.TransportTCP AS TransportTCP,
                                        sum(toUInt64(TransportTCPMap.Count)) AS cnt
                                      FROM $table
                                      ARRAY JOIN TransportTCPMap
                                      WHERE $timeFilter AND NodeID IN {nodesel}
                                      GROUP BY t,TransportTCP
                                      ORDER BY t
                                    )
                                    GROUP BY t,TransportTCP,cnt
                                    ORDER BY t,TransportTCP
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'A'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.QPSGraph(
                        title = 'Queries and responses by transport version',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Queries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT t, groupArray((if(TransportTCP,'TCP queries','UDP queries'), qc))
                                  FROM
                                  (
                                    SELECT
                                      t,TransportTCP,cnt/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        TransportTCPMap.TransportTCP AS TransportTCP,
                                        sum(toUInt64(TransportTCPMap.Count)) AS cnt
                                      FROM $table
                                      ARRAY JOIN TransportTCPMap
                                      WHERE $timeFilter AND NodeID IN {nodesel}
                                      GROUP BY t,TransportTCP
                                      ORDER BY t
                                    )
                                    GROUP BY t,TransportTCP,cnt
                                    ORDER BY t,TransportTCP
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'A'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Responses' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT t, groupArray((if(TransportTCP,'TCP responses','UDP responses'), qc))
                                  FROM
                                  (
                                    SELECT
                                      t,TransportTCP,cnt/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        TransportTCPMap.TransportTCP AS TransportTCP,
                                        sum(toUInt64(TransportTCPMap.Count)) AS cnt
                                      FROM $table
                                      ARRAY JOIN TransportTCPMap
                                      WHERE $timeFilter AND NodeID IN {nodesel}
                                      GROUP BY t,TransportTCP
                                      ORDER BY t
                                    )
                                    GROUP BY t,TransportTCP,cnt
                                    ORDER BY t,TransportTCP
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'B'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'QTYPE by IP version',
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = True,
                            yaxis = GCommon.BarChartAxis(
                                title = 'Queries per second',
                            ),
                        ),
                        autotrace = True,
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'QtypeIpVersion' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    notEmpty(QType) ? QType : concat('TYPE', toString(QueryType)) AS DisplayQType,
                                    multiIf(TransportIPv6, 'IPv6', 'IPv4'),
                                    sum(Cnt) / ($to - $from)
                                  FROM
                                  (
                                    SELECT
                                      TransportIPv6,
                                      QueryType,
                                      sum(Count) AS Cnt
                                    FROM $table
                                    WHERE $timeFilter
                                    AND NodeID IN {nodesel}
                                    GROUP BY
                                      TransportIPv6,
                                      QueryType
                                    ORDER BY TransportIPv6
                                  ) AS QTypeTransport
                                  ALL INNER JOIN
                                  (
                                    SELECT
                                      value_name AS QType,
                                      toUInt16(value) AS QueryType
                                    FROM {nodeinfo_database}.iana_text
                                    WHERE registry_name = 'QTYPE'
                                  ) AS QTypeName USING QueryType
                                  GROUP BY TransportIPv6, QueryType, QType
                                  ORDER BY DisplayQType""".format(
                                      nodesel=nodesel,
                                      nodeinfo_database=agginfo['nodeinfo_database'])),
                                refId = 'A'
                            )
                        ],
                    ),
                ],
            ),
        ]
    )
