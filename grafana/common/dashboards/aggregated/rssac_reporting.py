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
        title = "RSSAC Reporting",
        tags = [
            agginfo['graph_tag']
        ],
        uid = myuid,
        rows = [
            GCore.Row(
                panels = [
                    GCommon.QPMGraph(
                        title = 'RCODE volume',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Responses' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT t, groupArray((ResponseRcode, qc))
                                  FROM
                                  (
                                    SELECT
                                      t,ResponseRcode,60*cnt/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        ResponseRcodeMap.ResponseRcode AS ResponseRcode,
                                        sum(toUInt64(ResponseRcodeMap.Count)) AS cnt
                                      FROM $table
                                      ARRAY JOIN ResponseRcodeMap
                                      WHERE $timeFilter AND NodeID IN {nodesel}
                                      GROUP BY t, ResponseRcode
                                      ORDER BY t, ResponseRcode
                                    )
                                    GROUP BY t, ResponseRcode, cnt
                                    ORDER BY t, ResponseRcode
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
                    GCommon.BarChart(
                        title = 'DNS UDP Query size for sizes below 1000 bytes',
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = False,
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
                                color = '#1F60C4',
                                x = 'UDPQueryLen',
                                y = 'UDPQueryCnt',
                                text = 'UDPQueryCnt',
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
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'DNS TCP Query size for sizes below 1000 bytes',
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = False,
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
                                name = 'TCP Query',
                                color = '#1F60C4',
                                x = 'TCPQueryLen',
                                y = 'TCPQueryCnt',
                                text = 'TCPQueryCnt',
                            ),
                        ],
                        targets = [
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
                                refId = 'A'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'DNS UDP Response size for sizes below 1000 bytes',
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = False,
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
                                name = 'UDP Response',
                                color = '#1F60C4',
                                x = 'UDPResponseLen',
                                y = 'UDPResponseCnt',
                                text = 'UDPResponseCnt',
                            ),
                        ],
                        targets = [
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
                                refId = 'A'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'DNS TCP Response size for sizes below 1000 bytes',
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = False,
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
                                name = 'TCP Response',
                                color = '#1F60C4',
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
                                refId = 'A'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'DNS UDP Query size for sizes above 1000 bytes',
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = False,
                            xaxis = GCommon.BarChartAxis(
                                autotick = False,
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_LINEAR,
                                axrange = [1000, 3000],
                                tick0 = 1008,
                                dtick = 32,
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
                                color = '#FFB357',
                                x = 'UDPQueryLen',
                                y = 'UDPQueryCnt',
                                text = 'UDPQueryCnt',
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
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'DNS TCP Query size for sizes above 1000 bytes',
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = False,
                            xaxis = GCommon.BarChartAxis(
                                autotick = False,
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_LINEAR,
                                axrange = [1000, 3000],
                                tick0 = 1008,
                                dtick = 32,
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
                                name = 'TCP Query',
                                color = '#FFB357',
                                x = 'TCPQueryLen',
                                y = 'TCPQueryCnt',
                                text = 'TCPQueryCnt',
                            ),
                        ],
                        targets = [
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
                                refId = 'A'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'DNS UDP Response size for sizes above 1000 bytes',
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = False,
                            xaxis = GCommon.BarChartAxis(
                                autotick = False,
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_LINEAR,
                                axrange = [1000, 3000],
                                tick0 = 1008,
                                dtick = 32,
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
                                name = 'UDP Response',
                                color = '#FFB357',
                                x = 'UDPResponseLen',
                                y = 'UDPResponseCnt',
                                text = 'UDPResponseCnt',
                            ),
                        ],
                        targets = [
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
                                refId = 'A'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.BarChart(
                        title = 'DNS TCP Response size for sizes above 1000 bytes',
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = False,
                            xaxis = GCommon.BarChartAxis(
                                autotick = False,
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_LINEAR,
                                axrange = [1000, 3000],
                                tick0 = 1008,
                                dtick = 32,
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
                                refId = 'A'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.QPMGraph(
                        title = 'Queries and Responses, TCP/IPv4',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toUInt64(QueryCount))/{interval_divisor} AS Queries,
                                    60 * sum(toUInt64(ResponseCount))/{interval_divisor} AS Responses
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                  AND TransportTCP = 1
                                  AND TransportIPv6 = 0
                                  AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'A'
                            ),
                        ],
                    ),
                    GCommon.QPMGraph(
                        title = 'Queries and Responses, TCP/IPv6',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toUInt64(QueryCount))/{interval_divisor} AS Queries,
                                    60 * sum(toUInt64(ResponseCount))/{interval_divisor} AS Responses
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                  AND TransportTCP = 1
                                  AND TransportIPv6 <> 0
                                  AND NodeID IN {nodesel}
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
                    GCommon.QPMGraph(
                        title = 'Queries and Responses, UDP/IPv4',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toUInt64(QueryCount))/{interval_divisor} AS Queries,
                                    60 * sum(toUInt64(ResponseCount))/{interval_divisor} AS Responses
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                  AND TransportTCP = 0
                                  AND TransportIPv6 = 0
                                  AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'A'
                            ),
                        ],
                    ),
                    GCommon.QPMGraph(
                        title = 'Queries and Responses, UDP/IPv6',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toUInt64(QueryCount))/{interval_divisor} AS Queries,
                                    60 * sum(toUInt64(ResponseCount))/{interval_divisor} AS Responses
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                  AND TransportTCP = 0
                                  AND TransportIPv6 <> 0
                                  AND NodeID IN {nodesel}
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
                    GCommon.QPMGraph(
                        title = 'Difference in query and response volume, TCP/IPv4',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toInt64(QueryCount) - ResponseCount)/{interval_divisor} AS Difference
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                  AND TransportTCP = 1
                                  AND TransportIPv6 = 0
                                  AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'A'
                            ),
                        ],
                    ),
                    GCommon.QPMGraph(
                        title = 'Difference in query and response volume, TCP/IPv6',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toUInt64(QueryCount) - ResponseCount)/{interval_divisor} AS Difference
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                  AND TransportTCP = 1
                                  AND TransportIPv6 <> 0
                                  AND NodeID IN {nodesel}
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
                    GCommon.QPMGraph(
                        title = 'Difference in query and response volume, UDP/IPv4',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toInt64(QueryCount) - ResponseCount)/{interval_divisor} AS Difference
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                  AND TransportTCP = 0
                                  AND TransportIPv6 = 0
                                  AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'A'
                            ),
                        ],
                    ),
                    GCommon.QPMGraph(
                        title = 'Difference in query and response volume, UDP/IPv6',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toInt64(QueryCount) - ResponseCount)/{interval_divisor} AS Difference
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                  AND TransportTCP = 0
                                  AND TransportIPv6 <> 0
                                  AND NodeID IN {nodesel}
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
