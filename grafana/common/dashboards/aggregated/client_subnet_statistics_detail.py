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

def query_classification_chart(chart_title, yaxis_label, prefix_field, agginfo, nodesel):
    return GCommon.BarChart(
        title = chart_title,
        orientation = GCommon.BAR_CHART_ORIENTATION_HORIZONTAL,
        layout = GCommon.BarChartLayout(
            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
            showlegend = True,
            xaxis = GCommon.BarChartAxis(
                title = 'Queries per second',
            ),
            yaxis = GCommon.BarChartAxis(
                autotick = False,
                axtype = GCommon.BAR_CHART_AXIS_TYPE_CATEGORY,
                tickmargin = 110,
                title = yaxis_label,
            ),
        ),
        traces = [
            GCommon.BarChartTrace(
                name = 'AForA',
                x = 'AForA',
                y = 'AForAPrefix',
                text = 'AForA',
            ),
            GCommon.BarChartTrace(
                name = 'AForRoot',
                x = 'AForRoot',
                y = 'AForRootPrefix',
                text = 'AForRoot',
            ),
            GCommon.BarChartTrace(
                name = 'FunnyQueryClass',
                x = 'FunnyQueryClass',
                y = 'FunnyQueryClassPrefix',
                text = 'FunnyQueryClass',
            ),
            GCommon.BarChartTrace(
                name = 'FunnyQueryType',
                x = 'FunnyQueryType',
                y = 'FunnyQueryTypePrefix',
                text = 'FunnyQueryType',
            ),
            GCommon.BarChartTrace(
                name = 'Localhost',
                x = 'Localhost',
                y = 'LocalhostPrefix',
                text = 'Localhost',
            ),
            GCommon.BarChartTrace(
                name = 'NonAuthTld',
                x = 'NonAuthTld',
                y = 'NonAuthTldPrefix',
                text = 'NonAuthTld',
            ),
            GCommon.BarChartTrace(
                name = 'Ok',
                x = 'Ok',
                y = 'OkPrefix',
                text = 'Ok',
            ),
            GCommon.BarChartTrace(
                name = 'RFC1918Ptr',
                x = 'RFC1918Ptr',
                y = 'RFC1918PtrPrefix',
                text = 'RFC1918Ptr',
            ),
            GCommon.BarChartTrace(
                name = 'RootServersNet',
                x = 'RootServersNet',
                y = 'RootServersNetPrefix',
                text = 'RootServersNet',
            ),
            GCommon.BarChartTrace(
                name = 'SrcPortZero',
                x = 'SrcPortZero',
                y = 'SrcPortZeroPrefix',
                text = 'SrcPortZero',
            ),
        ],
        targets = [
            GCommon.ClickHouseTableTarget(
                database = agginfo['database'],
                table = 'QueryClassifications' + agginfo['table_suffix'],
                round = agginfo['round'],
                query = textwrap.dedent("""\
                  SELECT
                    Prefix AS AForAPrefix,
                    AForA,
                    Count
                  FROM
                  (
                    SELECT
                      {prefix_field} AS Prefix,
                      sum(Count) AS Count,
                      sum(AForACount)/($to - $from) AS AForA
                    FROM $table
                    WHERE $timeFilter
                    AND NodeID IN {nodesel}
                    GROUP BY Prefix
                    ORDER BY Count DESC
                    LIMIT 40
                  )
                  ORDER BY Count ASC
                  """.format(
                          prefix_field=prefix_field,
                          nodesel=nodesel,
                          nodeinfo_database=agginfo['nodeinfo_database'])),
                refId = 'A'
            ),
            GCommon.ClickHouseTableTarget(
                database = agginfo['database'],
                table = 'QueryClassifications' + agginfo['table_suffix'],
                round = agginfo['round'],
                query = textwrap.dedent("""\
                  SELECT
                    Prefix AS AForRootPrefix,
                    AForRoot,
                    Count
                  FROM
                  (
                    SELECT
                      {prefix_field} AS Prefix,
                      sum(Count) AS Count,
                      sum(AForRootCount)/($to - $from) AS AForRoot
                    FROM $table
                    WHERE $timeFilter
                    AND NodeID IN {nodesel}
                    GROUP BY Prefix
                    ORDER BY Count DESC
                    LIMIT 40
                  )
                  ORDER BY Count ASC
                  """.format(
                          prefix_field=prefix_field,
                          nodesel=nodesel,
                          nodeinfo_database=agginfo['nodeinfo_database'])),
                refId = 'B'
            ),
            GCommon.ClickHouseTableTarget(
                database = agginfo['database'],
                table = 'QueryClassifications' + agginfo['table_suffix'],
                round = agginfo['round'],
                query = textwrap.dedent("""\
                  SELECT
                    Prefix AS FunnyQueryClassPrefix,
                    FunnyQueryClass,
                    Count
                  FROM
                  (
                    SELECT
                      {prefix_field} AS Prefix,
                      sum(Count) AS Count,
                      sum(FunnyQueryClassCount)/($to - $from) AS FunnyQueryClass
                    FROM $table
                    WHERE $timeFilter
                    AND NodeID IN {nodesel}
                    GROUP BY Prefix
                    ORDER BY Count DESC
                    LIMIT 40
                  )
                  ORDER BY Count ASC
                  """.format(
                          prefix_field=prefix_field,
                          nodesel=nodesel,
                          nodeinfo_database=agginfo['nodeinfo_database'])),
                refId = 'C'
            ),
            GCommon.ClickHouseTableTarget(
                database = agginfo['database'],
                table = 'QueryClassifications' + agginfo['table_suffix'],
                round = agginfo['round'],
                query = textwrap.dedent("""\
                  SELECT
                    Prefix AS FunnyQueryTypePrefix,
                    FunnyQueryType,
                    Count
                  FROM
                  (
                    SELECT
                      {prefix_field} AS Prefix,
                      sum(Count) AS Count,
                      sum(FunnyQueryTypeCount)/($to - $from) AS FunnyQueryType
                    FROM $table
                    WHERE $timeFilter
                    AND NodeID IN {nodesel}
                    GROUP BY Prefix
                    ORDER BY Count DESC
                    LIMIT 40
                  )
                  ORDER BY Count DESC
                  """.format(
                          prefix_field=prefix_field,
                          nodesel=nodesel,
                          nodeinfo_database=agginfo['nodeinfo_database'])),
                refId = 'D'
            ),
            GCommon.ClickHouseTableTarget(
                database = agginfo['database'],
                table = 'QueryClassifications' + agginfo['table_suffix'],
                round = agginfo['round'],
                query = textwrap.dedent("""\
                  SELECT
                    Prefix AS LocalhostPrefix,
                    Localhost,
                    Count
                  FROM
                  (
                    SELECT
                      {prefix_field} AS Prefix,
                      sum(Count) AS Count,
                      sum(LocalhostCount)/($to - $from) AS Localhost
                    FROM $table
                    WHERE $timeFilter
                    AND NodeID IN {nodesel}
                    GROUP BY Prefix
                    ORDER BY Count DESC
                    LIMIT 40
                  )
                  ORDER BY Count ASC
                  """.format(
                          prefix_field=prefix_field,
                          nodesel=nodesel,
                          nodeinfo_database=agginfo['nodeinfo_database'])),
                refId = 'E'
            ),
            GCommon.ClickHouseTableTarget(
                database = agginfo['database'],
                table = 'QueryClassifications' + agginfo['table_suffix'],
                round = agginfo['round'],
                query = textwrap.dedent("""\
                  SELECT
                    Prefix AS NonAuthTldPrefix,
                    NonAuthTld,
                    Count
                  FROM
                  (
                    SELECT
                      {prefix_field} AS Prefix,
                      sum(Count) AS Count,
                      sum(NonAuthTldCount)/($to - $from) AS NonAuthTld
                    FROM $table
                    WHERE $timeFilter
                    AND NodeID IN {nodesel}
                    GROUP BY Prefix
                    ORDER BY Count DESC
                    LIMIT 40
                  )
                  ORDER BY Count ASC
                  """.format(
                          prefix_field=prefix_field,
                          nodesel=nodesel,
                          nodeinfo_database=agginfo['nodeinfo_database'])),
                refId = 'F'
            ),
            GCommon.ClickHouseTableTarget(
                database = agginfo['database'],
                table = 'QueryClassifications' + agginfo['table_suffix'],
                round = agginfo['round'],
                query = textwrap.dedent("""\
                  SELECT
                    Prefix AS OkPrefix,
                    Ok,
                    TotalCount
                  FROM
                  (
                    SELECT
                      {prefix_field} AS Prefix,
                      sum(Count) AS TotalCount,
                      sum(Count -
                            (AForACount +
                             AForRootCount +
                             FunnyQueryClassCount +
                             FunnyQueryTypeCount +
                             LocalhostCount +
                             NonAuthTldCount +
                             RFC1918PtrCount +
                             RootServersNetCount +
                             SrcPortZeroCount))/($to - $from) AS Ok
                    FROM $table
                    WHERE $timeFilter
                    AND NodeID IN {nodesel}
                    GROUP BY Prefix
                    ORDER BY TotalCount DESC
                    LIMIT 40
                  )
                  ORDER BY TotalCount ASC
                  """.format(
                          prefix_field=prefix_field,
                          nodesel=nodesel,
                          nodeinfo_database=agginfo['nodeinfo_database'])),
                refId = 'G'
            ),
            GCommon.ClickHouseTableTarget(
                database = agginfo['database'],
                table = 'QueryClassifications' + agginfo['table_suffix'],
                round = agginfo['round'],
                query = textwrap.dedent("""\
                  SELECT
                    Prefix AS RFC1918PtrPrefix,
                    RFC1918Ptr,
                    Count
                  FROM
                  (
                    SELECT
                      {prefix_field} AS Prefix,
                      sum(Count) AS Count,
                      sum(RFC1918PtrCount)/($to - $from) AS RFC1918Ptr
                    FROM $table
                    WHERE $timeFilter
                    AND NodeID IN {nodesel}
                    GROUP BY Prefix
                    ORDER BY Count DESC
                    LIMIT 40
                  )
                  ORDER BY Count ASC
                  """.format(
                          prefix_field=prefix_field,
                          nodesel=nodesel,
                          nodeinfo_database=agginfo['nodeinfo_database'])),
                refId = 'H'
            ),
            GCommon.ClickHouseTableTarget(
                database = agginfo['database'],
                table = 'QueryClassifications' + agginfo['table_suffix'],
                round = agginfo['round'],
                query = textwrap.dedent("""\
                  SELECT
                    Prefix AS RootServersNetPrefix,
                    RootServersNet,
                    Count
                  FROM
                  (
                    SELECT
                      {prefix_field} AS Prefix,
                      sum(Count) AS Count,
                      sum(RootServersNetCount)/($to - $from) AS RootServersNet
                    FROM $table
                    WHERE $timeFilter
                    AND NodeID IN {nodesel}
                    GROUP BY Prefix
                    ORDER BY Count DESC
                    LIMIT 40
                  )
                  ORDER BY Count ASC
                  """.format(
                          prefix_field=prefix_field,
                          nodesel=nodesel,
                          nodeinfo_database=agginfo['nodeinfo_database'])),
                refId = 'I'
            ),
            GCommon.ClickHouseTableTarget(
                database = agginfo['database'],
                table = 'QueryClassifications' + agginfo['table_suffix'],
                round = agginfo['round'],
                query = textwrap.dedent("""\
                  SELECT
                    Prefix AS SrcPortZeroPrefix,
                    SrcPortZero,
                    Count
                  FROM
                  (
                    SELECT
                      {prefix_field} AS Prefix,
                      sum(Count) AS Count,
                      sum(SrcPortZeroCount)/($to - $from) AS SrcPortZero
                    FROM $table
                    WHERE $timeFilter
                    AND NodeID IN {nodesel}
                    GROUP BY Prefix
                    ORDER BY Count DESC
                    LIMIT 40
                  )
                  ORDER BY Count ASC
                  """.format(
                          prefix_field=prefix_field,
                          nodesel=nodesel,
                          nodeinfo_database=agginfo['nodeinfo_database'])),
                refId = 'J'
            ),
        ],
    )


def dash(myuid, agginfo, nodesel, **kwargs):
    return GCommon.Dashboard(
        title = "Client subnet statistics detail",
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
                height = GCore.Pixels(GCore.DEFAULT_ROW_HEIGHT.num * 2),
                panels = [
                    GCommon.BarChart(
                        title = 'Clients by fixed subnet',
                        orientation = GCommon.BAR_CHART_ORIENTATION_HORIZONTAL,
                        layout = GCommon.BarChartLayout(
                            xaxis = GCommon.BarChartAxis(
                                title = 'Queries per second',
                            ),
                            yaxis = GCommon.BarChartAxis(
                                autotick = False,
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_CATEGORY,
                                tickmargin = 110,
                                title = 'Fixed Subnet',
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
                                table = 'BusiestClientSubnets' + agginfo['table_suffix'],
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
            GCore.Row(
                height = GCore.Pixels(GCore.DEFAULT_ROW_HEIGHT.num * 2),
                panels = [
                    GCommon.BarChart(
                        title = 'RCODE by clients by ASN',
                        orientation = GCommon.BAR_CHART_ORIENTATION_HORIZONTAL,
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = True,
                            xaxis = GCommon.BarChartAxis(
                                title = 'Queries per second',
                            ),
                            yaxis = GCommon.BarChartAxis(
                                autotick = False,
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_CATEGORY,
                                tickmargin = 110,
                                title = 'ASN',
                            ),
                        ),
                        autotrace = True,
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'BusiestClientSubnets' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      notEmpty(rcodeText) ? rcodeText : concat('RCODE', toString(rcode)) AS DisplayRcode,
                                      sum(rcodeCount) / ($to - $from) AS rcodeCount,
                                      ClientASN
                                  FROM
                                  (
                                      SELECT
                                          ClientASN,
                                          rcode,
                                          sum(rcodeCount) AS rcodeCount,
                                          any(sCount) AS sCount
                                      FROM
                                      (
                                          SELECT
                                              ClientASN,
                                              sum(RcodeMap.Count) AS sCount
                                          FROM $table
                                          ARRAY JOIN RcodeMap
                                          WHERE $timeFilter
                                              AND NodeID IN {nodesel}
                                          GROUP BY
                                              ClientASN
                                          ORDER BY sCount DESC, ClientASN ASC
                                          LIMIT 30
                                      ) AS ClientASNCounts
                                      ALL LEFT JOIN
                                      (
                                          SELECT
                                              ClientASN,
                                              RcodeMap.ResponseRcode AS rcode,
                                              sum(RcodeMap.Count) AS rcodeCount
                                          FROM $table
                                          ARRAY JOIN RcodeMap
                                          WHERE
                                              $timeFilter
                                              AND NodeID IN {nodesel}
                                          GROUP BY
                                              ClientASN,
                                              rcode
                                          UNION ALL
                                          (
                                              SELECT
                                                  ClientASN,
                                                  rcode,
                                                  CAST(0 AS UInt64) AS rcodeCount
                                              FROM
                                              (
                                                  SELECT
                                                      0 AS Zero,
                                                      ClientASN
                                                  FROM $table
                                                  WHERE
                                                      $timeFilter
                                                      AND NodeID IN {nodesel}
                                                  GROUP BY ClientASN
                                              ) AS ZeroClientASN
                                              ALL LEFT JOIN
                                              (
                                                  SELECT
                                                      0 AS Zero,
                                                      RcodeMap.ResponseRcode AS rcode
                                                  FROM $table
                                                  ARRAY JOIN RcodeMap
                                                  WHERE
                                                    $timeFilter
                                                    AND NodeID IN {nodesel}
                                                  GROUP BY rcode
                                              ) AS ZeroRcode USING Zero
                                          )
                                      ) AS ClientASNRcodeCounts USING ClientASN
                                      GROUP BY
                                          ClientASN,
                                          rcode
                                  ) AS ClientASNRcodeCountsTotal
                                  ALL INNER JOIN
                                  (
                                      SELECT
                                          value_name AS rcodeText,
                                          toUInt16(value) AS rcode
                                      FROM {nodeinfo_database}.iana_text
                                      WHERE registry_name = 'RCODE'
                                  ) AS ClientASNNameCountsTotal USING rcode
                                  GROUP BY
                                      ClientASN,
                                      rcode,
                                      rcodeText
                                  ORDER BY
                                      sum(sCount) ASC,
                                      rcodeText ASC,
                                      ClientASN DESC""".format(
                                          nodesel=nodesel,
                                          nodeinfo_database=agginfo['nodeinfo_database'])),
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
                        title = 'RCODE by clients by AS subnet',
                        orientation = GCommon.BAR_CHART_ORIENTATION_HORIZONTAL,
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = True,
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
                        autotrace = True,
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'BGPPrefix' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      notEmpty(rcodeText) ? rcodeText : concat('RCODE', toString(rcode)) AS DisplayRcode,
                                      sum(rcodeCount) / ($to - $from) AS rcodeCount,
                                      Prefix
                                  FROM
                                  (
                                      SELECT
                                          Prefix,
                                          rcode,
                                          sum(rcodeCount) AS rcodeCount,
                                          any(sCount) AS sCount
                                      FROM
                                      (
                                          SELECT
                                              Prefix,
                                              sum(RcodeMap.Count) AS sCount
                                          FROM $table
                                          ARRAY JOIN RcodeMap
                                          WHERE $timeFilter
                                              AND NodeID IN {nodesel}
                                          GROUP BY
                                              Prefix
                                          ORDER BY sCount DESC, Prefix ASC
                                          LIMIT 30
                                      ) AS PrefixCount
                                      ALL LEFT JOIN
                                      (
                                          SELECT
                                              Prefix,
                                              RcodeMap.ResponseRcode AS rcode,
                                              sum(RcodeMap.Count) AS rcodeCount
                                          FROM $table
                                          ARRAY JOIN RcodeMap
                                          WHERE
                                              $timeFilter
                                              AND NodeID IN {nodesel}
                                          GROUP BY
                                              Prefix,
                                              rcode
                                          UNION ALL
                                          (
                                              SELECT
                                                  Prefix,
                                                  rcode,
                                                  CAST(0 AS UInt64) AS rcodeCount
                                              FROM
                                              (
                                                  SELECT
                                                      0 AS Zero,
                                                      Prefix
                                                  FROM $table
                                                  WHERE
                                                      $timeFilter
                                                      AND NodeID IN {nodesel}
                                                  GROUP BY Prefix
                                              ) AS ZeroPrefox
                                              ALL LEFT JOIN
                                              (
                                                  SELECT
                                                      0 AS Zero,
                                                      RcodeMap.ResponseRcode AS rcode
                                                  FROM $table
                                                  ARRAY JOIN RcodeMap
                                                  WHERE
                                                    $timeFilter
                                                    AND NodeID IN {nodesel}
                                                  GROUP BY rcode
                                              ) AS ZeroRcode USING Zero
                                          )
                                      ) AS PrefixRcodeCounts USING Prefix
                                      GROUP BY
                                          Prefix,
                                          rcode
                                  ) AS PrefixRcodeCountsTotal
                                  ALL INNER JOIN
                                  (
                                      SELECT
                                          value_name AS rcodeText,
                                          toUInt16(value) AS rcode
                                      FROM {nodeinfo_database}.iana_text
                                      WHERE registry_name = 'RCODE'
                                  ) AS PrefixNameCountsTotal USING rcode
                                  GROUP BY
                                      Prefix,
                                      rcode,
                                      rcodeText
                                  ORDER BY
                                      sum(sCount) ASC,
                                      rcodeText ASC,
                                      Prefix DESC""".format(
                                          nodesel=nodesel,
                                          nodeinfo_database=agginfo['nodeinfo_database'])),
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
                        title = 'RCODE by clients by fixed subnet',
                        orientation = GCommon.BAR_CHART_ORIENTATION_HORIZONTAL,
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = True,
                            xaxis = GCommon.BarChartAxis(
                                title = 'Queries per second',
                            ),
                            yaxis = GCommon.BarChartAxis(
                                autotick = False,
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_CATEGORY,
                                tickmargin = 110,
                                title = 'Fixed Subnet',
                            ),
                        ),
                        autotrace = True,
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'BusiestClientSubnets' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      notEmpty(rcodeText) ? rcodeText : concat('RCODE', toString(rcode)) AS DisplayRcode,
                                      sum(rcodeCount) / ($to - $from) AS rcodeCount,
                                      Prefix
                                  FROM
                                  (
                                      SELECT
                                          Prefix,
                                          rcode,
                                          sum(rcodeCount) AS rcodeCount,
                                          any(sCount) AS sCount
                                      FROM
                                      (
                                          SELECT
                                              Prefix,
                                              sum(RcodeMap.Count) AS sCount
                                          FROM $table
                                          ARRAY JOIN RcodeMap
                                          WHERE $timeFilter
                                              AND NodeID IN {nodesel}
                                          GROUP BY
                                              Prefix
                                          ORDER BY sCount DESC, Prefix ASC
                                          LIMIT 30
                                      ) AS PrefixCount
                                      ALL LEFT JOIN
                                      (
                                          SELECT
                                              Prefix,
                                              RcodeMap.ResponseRcode AS rcode,
                                              sum(RcodeMap.Count) AS rcodeCount
                                          FROM $table
                                          ARRAY JOIN RcodeMap
                                          WHERE
                                              $timeFilter
                                              AND NodeID IN {nodesel}
                                          GROUP BY
                                              Prefix,
                                              rcode
                                          UNION ALL
                                          (
                                              SELECT
                                                  Prefix,
                                                  rcode,
                                                  CAST(0 AS UInt64) AS rcodeCount
                                              FROM
                                              (
                                                  SELECT
                                                      0 AS Zero,
                                                      Prefix
                                                  FROM $table
                                                  WHERE
                                                      $timeFilter
                                                      AND NodeID IN {nodesel}
                                                  GROUP BY Prefix
                                              ) AS ZeroPrefix
                                              ALL LEFT JOIN
                                              (
                                                  SELECT
                                                      0 AS Zero,
                                                      RcodeMap.ResponseRcode AS rcode
                                                  FROM $table
                                                  ARRAY JOIN RcodeMap
                                                  WHERE
                                                    $timeFilter
                                                    AND NodeID IN {nodesel}
                                                  GROUP BY rcode
                                              ) AS ZeroRcode USING Zero
                                          )
                                      ) AS PrefixRcodeCounts USING Prefix
                                      GROUP BY
                                          Prefix,
                                          rcode
                                  ) AS PrefixRcodeCountsTotal
                                  ALL INNER JOIN
                                  (
                                      SELECT
                                          value_name AS rcodeText,
                                          toUInt16(value) AS rcode
                                      FROM {nodeinfo_database}.iana_text
                                      WHERE registry_name = 'RCODE'
                                  ) AS PrefixNameCountsTotal USING rcode
                                  GROUP BY
                                      Prefix,
                                      rcode,
                                      rcodeText
                                  ORDER BY
                                      sum(sCount) ASC,
                                      rcodeText ASC,
                                      Prefix DESC""".format(
                                          nodesel=nodesel,
                                          nodeinfo_database=agginfo['nodeinfo_database'])),
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
                        title = 'Root abusers by fixed subnet',
                        orientation = GCommon.BAR_CHART_ORIENTATION_HORIZONTAL,
                        layout = GCommon.BarChartLayout(
                            xaxis = GCommon.BarChartAxis(
                                title = 'Queries per second',
                            ),
                            yaxis = GCommon.BarChartAxis(
                                autotick = False,
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_CATEGORY,
                                tickmargin = 110,
                                title = 'Fixed Subnet',
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
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      Subnet,
                                      QPS
                                  FROM
                                  (
                                      SELECT
                                          FixedPrefix AS Subnet,
                                          sum(RootAbuseCount)/($to - $from) AS QPS
                                      FROM $table
                                      WHERE $timeFilter
                                          AND NodeID IN {nodesel}
                                      GROUP BY FixedPrefix
                                      ORDER BY QPS DESC
                                      LIMIT 40
                                  )
                                  ORDER BY QPS ASC""".format(
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
                    query_classification_chart(
                        'Query classification by busiest fixed subnet',
                        'Fixed Subnet',
                        'FixedPrefix',
                        agginfo,
                        nodesel)
                ],
            ),
            GCore.Row(
                height = GCore.Pixels(GCore.DEFAULT_ROW_HEIGHT.num * 2),
                panels = [
                    query_classification_chart(
                        'Query classification by busiest ASN',
                        'ASN',
                        'ClientASN',
                        agginfo,
                        nodesel)
                ],
            ),
            GCore.Row(
                height = GCore.Pixels(GCore.DEFAULT_ROW_HEIGHT.num * 2),
                panels = [
                    query_classification_chart(
                        'Query classification by busiest AS subnet',
                        'AS subnet',
                        'ASPrefix',
                        agginfo,
                        nodesel)
                ],
            ),
        ]
    )
