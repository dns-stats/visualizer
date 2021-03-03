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
        title = "RSSAC other graphs",
        tags = [
            agginfo['graph_tag']
        ],
        uid = myuid,
        rows = [
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'DNS Query and Response sizes by transport for sizes below 1000 bytes',
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = True,
                            xaxis = GCommon.BarChartAxis(
                                autotick = False,
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_LINEAR,
                                axrange = [0, 1000],
                                tick0 = 16,
                                dtick = 16,
                                tickangle = -45,
                                tickmargin = 40,
                                title = 'Message size (bytes)',
                            ),
                            yaxis = GCommon.BarChartAxis(
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_LINEAR,
                                dtick = 16,
                                rangemode = GCommon.BAR_CHART_AXIS_RANGEMODE_TOZERO,
                                title = 'Messages per minute',
                            ),
                        ),
                        traces = [
                            GCommon.BarChartTrace(
                                name = 'UDP Query',
                                color = '#8AB8FF',
                                x = 'UDPQueryLen',
                                y = 'UDPQueryCnt',
                                text = 'UDPQueryCnt',
                            ),
                            GCommon.BarChartTrace(
                                name = 'TCP Query',
                                color = '#FA6400',
                                x = 'TCPQueryLen',
                                y = 'TCPQueryCnt',
                                text = 'TCPQueryCnt',
                            ),
                            GCommon.BarChartTrace(
                                name = 'UDP Response',
                                color = '#1F60C4',
                                x = 'UDPResponseLen',
                                y = 'UDPResponseCnt',
                                text = 'UDPResponseCnt',
                            ),
                            GCommon.BarChartTrace(
                                name = 'TCP Response',
                                color = '#FFB357',
                                x = 'TCPResponseLen',
                                y = 'TCPResponseCnt',
                                text = 'TCPResponseCnt',
                            ),
                        ],
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseLength' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      Len + intDiv({bucketsize}, 2) AS UDPQueryLen,
                                      60 * sum(Cnt)/($to - $from) AS UDPQueryCnt
                                  FROM
                                  (
                                      SELECT
                                          intDiv(QueryLengthMap.Length, {bucketsize})*{bucketsize} AS Len,
                                          sum(toUInt64(QueryLengthMap.Count)) AS Cnt
                                      FROM $table
                                      ARRAY JOIN QueryLengthMap
                                      WHERE $timeFilter
                                      AND TransportTCP=0
                                      AND NodeID IN {nodesel}
                                      AND Len < 1000
                                      GROUP BY Len
                                      UNION ALL
                                      (
                                          SELECT
                                              CAST(number*{bucketsize} AS UInt16) AS Len,
                                              CAST(0 AS UInt64) AS Cnt
                                          FROM system.numbers
                                          WHERE number > 0 LIMIT {bucketlen}
                                      )
                                  )
                                  GROUP BY Len""".format(
                                      nodesel=nodesel,
                                      bucketsize=16, bucketlen=1000//16)),
                                refId = 'A'
                            ),
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseLength' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      Len + intDiv({bucketsize}, 2) AS TCPQueryLen,
                                      60 * sum(Cnt)/($to - $from) AS TCPQueryCnt
                                  FROM
                                  (
                                      SELECT
                                          intDiv(QueryLengthMap.Length, {bucketsize})*{bucketsize} AS Len,
                                          sum(toUInt64(QueryLengthMap.Count)) AS Cnt
                                      FROM $table
                                      ARRAY JOIN QueryLengthMap
                                      WHERE $timeFilter
                                      AND TransportTCP=1
                                      AND NodeID IN {nodesel}
                                      AND Len < 1000
                                      GROUP BY Len
                                      UNION ALL
                                      (
                                          SELECT
                                              CAST(number*{bucketsize} AS UInt16) AS Len,
                                              CAST(0 AS UInt64) AS Cnt
                                          FROM system.numbers
                                          WHERE number > 0 LIMIT {bucketlen}
                                      )
                                  )
                                  GROUP BY Len""".format(
                                      nodesel=nodesel,
                                      bucketsize=16, bucketlen=1000//16)),
                                refId = 'B'
                            ),
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseLength' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      Len + intDiv({bucketsize}, 2) AS UDPResponseLen,
                                      60 * sum(Cnt)/($to - $from) AS UDPResponseCnt
                                  FROM
                                  (
                                      SELECT
                                          intDiv(ResponseLengthMap.Length, {bucketsize})*{bucketsize} AS Len,
                                          sum(toUInt64(ResponseLengthMap.Count)) AS Cnt
                                      FROM $table
                                      ARRAY JOIN ResponseLengthMap
                                      WHERE $timeFilter
                                      AND TransportTCP=0
                                      AND NodeID IN {nodesel}
                                      AND Len < 1000
                                      GROUP BY Len
                                      UNION ALL
                                      (
                                          SELECT
                                              CAST(number*{bucketsize} AS UInt16) AS Len,
                                              CAST(0 AS UInt64) AS Cnt
                                          FROM system.numbers
                                          WHERE number > 0 LIMIT {bucketlen}
                                      )
                                  )
                                  GROUP BY Len""".format(
                                      nodesel=nodesel,
                                      bucketsize=16, bucketlen=1000//16)),
                                refId = 'C'
                            ),
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseLength' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      Len + intDiv({bucketsize}, 2) AS TCPResponseLen,
                                      60 * sum(Cnt)/($to - $from) AS TCPResponseCnt
                                  FROM
                                  (
                                      SELECT
                                          intDiv(ResponseLengthMap.Length, {bucketsize})*{bucketsize} AS Len,
                                          sum(toUInt64(ResponseLengthMap.Count)) AS Cnt
                                      FROM $table
                                      ARRAY JOIN ResponseLengthMap
                                      WHERE $timeFilter
                                      AND TransportTCP=1
                                      AND NodeID IN {nodesel}
                                      AND Len < 1000
                                      GROUP BY Len
                                      UNION ALL
                                      (
                                          SELECT
                                              CAST(number*{bucketsize} AS UInt16) AS Len,
                                              CAST(0 AS UInt64) AS Cnt
                                          FROM system.numbers
                                          WHERE number > 0 LIMIT {bucketlen}
                                      )
                                  )
                                  GROUP BY Len""".format(
                                      nodesel=nodesel,
                                      bucketsize=16, bucketlen=1000//16)),
                                refId = 'D'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'DNS Query and Response sizes by transport for sizes above 1000 bytes',
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = True,
                            xaxis = GCommon.BarChartAxis(
                                autotick = False,
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_LINEAR,
                                axrange = [1000, 3000],
                                tick0 = 1008,
                                dtick = 16,
                                tickangle = -90,
                                tickmargin = 45,
                                title = 'Message size (bytes)',
                            ),
                            yaxis = GCommon.BarChartAxis(
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_LINEAR,
                                dtick = 16,
                                rangemode = GCommon.BAR_CHART_AXIS_RANGEMODE_TOZERO,
                                title = 'Messages per minute',
                            ),
                        ),
                        traces = [
                            GCommon.BarChartTrace(
                                name = 'UDP Query',
                                color = '#8AB8FF',
                                x = 'UDPQueryLen',
                                y = 'UDPQueryCnt',
                                text = 'UDPQueryCnt',
                            ),
                            GCommon.BarChartTrace(
                                name = 'TCP Query',
                                color = '#FA6400',
                                x = 'TCPQueryLen',
                                y = 'TCPQueryCnt',
                                text = 'TCPQueryCnt',
                            ),
                            GCommon.BarChartTrace(
                                name = 'UDP Response',
                                color = '#1F60C4',
                                x = 'UDPResponseLen',
                                y = 'UDPResponseCnt',
                                text = 'UDPResponseCnt',
                            ),
                            GCommon.BarChartTrace(
                                name = 'TCP Response',
                                color = '#FFB357',
                                x = 'TCPResponseLen',
                                y = 'TCPResponseCnt',
                                text = 'TCPResponseCnt',
                            ),
                        ],
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseLength' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      Len + intDiv({bucketsize}, 2) AS UDPQueryLen,
                                      60 * sum(Cnt)/($to - $from) AS UDPQueryCnt
                                  FROM
                                  (
                                      SELECT
                                          intDiv(QueryLengthMap.Length, {bucketsize})*{bucketsize} AS Len,
                                          sum(toUInt64(QueryLengthMap.Count)) AS Cnt
                                      FROM $table
                                      ARRAY JOIN QueryLengthMap
                                      WHERE $timeFilter
                                      AND TransportTCP=0
                                      AND NodeID IN {nodesel}
                                      AND Len >= 1000
                                      GROUP BY Len
                                      UNION ALL
                                      (
                                          SELECT
                                              CAST((number + intDiv(1000, {bucketsize}))*{bucketsize} AS UInt16) AS Len,
                                              CAST(0 AS UInt64) AS Cnt
                                          FROM system.numbers
                                          WHERE number > 0 LIMIT {bucketlen}
                                      )
                                  )
                                  GROUP BY Len""".format(
                                      nodesel=nodesel,
                                      bucketsize=16, bucketlen=2000//16)),
                                refId = 'A'
                            ),
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseLength' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      Len + intDiv({bucketsize}, 2) AS TCPQueryLen,
                                      60 * sum(Cnt)/($to - $from) AS TCPQueryCnt
                                  FROM
                                  (
                                      SELECT
                                          intDiv(QueryLengthMap.Length, {bucketsize})*{bucketsize} AS Len,
                                          sum(toUInt64(QueryLengthMap.Count)) AS Cnt
                                      FROM $table
                                      ARRAY JOIN QueryLengthMap
                                      WHERE $timeFilter
                                      AND TransportTCP=1
                                      AND NodeID IN {nodesel}
                                      AND Len >= 1000
                                      GROUP BY Len
                                      UNION ALL
                                      (
                                          SELECT
                                              CAST((number + intDiv(1000, {bucketsize}))*{bucketsize} AS UInt16) AS Len,
                                              CAST(0 AS UInt64) AS Cnt
                                          FROM system.numbers
                                          WHERE number > 0 LIMIT {bucketlen}
                                      )
                                  )
                                  GROUP BY Len""".format(
                                      nodesel=nodesel,
                                      bucketsize=16, bucketlen=2000//16)),
                                refId = 'B'
                            ),
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseLength' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      Len + intDiv({bucketsize}, 2) AS UDPResponseLen,
                                      60 * sum(Cnt)/($to - $from) AS UDPResponseCnt
                                  FROM
                                  (
                                      SELECT
                                          intDiv(ResponseLengthMap.Length, {bucketsize})*{bucketsize} AS Len,
                                          sum(toUInt64(ResponseLengthMap.Count)) AS Cnt
                                      FROM $table
                                      ARRAY JOIN ResponseLengthMap
                                      WHERE $timeFilter
                                      AND TransportTCP=0
                                      AND NodeID IN {nodesel}
                                      AND Len >= 1000
                                      GROUP BY Len
                                      UNION ALL
                                      (
                                          SELECT
                                              CAST((number + intDiv(1000, {bucketsize}))*{bucketsize} AS UInt16) AS Len,
                                              CAST(0 AS UInt64) AS Cnt
                                          FROM system.numbers
                                          WHERE number > 0 LIMIT {bucketlen}
                                      )
                                  )
                                  GROUP BY Len""".format(
                                      nodesel=nodesel,
                                      bucketsize=16, bucketlen=2000//16)),
                                refId = 'C'
                            ),
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseLength' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      Len + intDiv({bucketsize}, 2) AS TCPResponseLen,
                                      60 * sum(Cnt)/($to - $from) AS TCPResponseCnt
                                  FROM
                                  (
                                      SELECT
                                          intDiv(ResponseLengthMap.Length, {bucketsize})*{bucketsize} AS Len,
                                          sum(toUInt64(ResponseLengthMap.Count)) AS Cnt
                                      FROM $table
                                      ARRAY JOIN ResponseLengthMap
                                      WHERE $timeFilter
                                      AND TransportTCP=1
                                      AND NodeID IN {nodesel}
                                      AND Len >= 1000
                                      GROUP BY Len
                                      UNION ALL
                                      (
                                          SELECT
                                              CAST((number + intDiv(1000, {bucketsize}))*{bucketsize} AS UInt16) AS Len,
                                              CAST(0 AS UInt64) AS Cnt
                                          FROM system.numbers
                                          WHERE number > 0 LIMIT {bucketlen}
                                      )
                                  )
                                  GROUP BY Len""".format(
                                      nodesel=nodesel,
                                      bucketsize=16, bucketlen=2000//16)),
                                refId = 'D'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'Zone Load Time',
                        plottype = GCommon.PLOTLY_CHART_TYPE_SCATTER,
                        layout = GCommon.BarChartLayout(
                            xaxis = GCommon.BarChartAxis(
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_CATEGORY,
                                title = 'Serial number',
                            ),
                            yaxis = GCommon.BarChartAxis(
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_LINEAR,
                                title = 'Load time (s)',
                            ),
                        ),
                        traces = [
                            GCommon.BarChartTrace(
                                name = 'Latencies',
                                color = '#33B5E5',
                                x = 'Serial',
                                y = 'Latency',
                                text = 'Name',
                                showmarkers = True,
                            ),
                        ],
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['raw_database'],
                                table = 'ZoneLatency',
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      Serial, Latency, Name
                                  FROM $table
                                  ALL INNER JOIN
                                  (
                                      SELECT
                                          {name_col} AS Name,
                                          node_id AS NodeID
                                      FROM {nodeinfo_database}.node_text
                                  ) AS NodeName USING NodeID
                                  WHERE $timeFilter
                                  AND NodeID IN {nodesel}
                                  ORDER BY Serial ASC""".format(
                                      nodesel=nodesel,
                                      name_col=kwargs['zone_load_name_col'],
                                      nodeinfo_database=agginfo['nodeinfo_database'])),
                                refId = 'A'
                            ),
                        ],
                    ),
                ],
            ),
        ]
    )
