# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Aggregation QTYPE vs TLD plots

import textwrap

import grafanalib.core as GCore

import grafanacommon as GCommon

def dash(myuid, agginfo, nodesel, **kwargs):
    return GCommon.Dashboard(
        title = "QTYPE vs TLD",
        tags = [
            agginfo['graph_tag']
        ],
        uid = myuid,
        rows = [
            GCore.Row(
                height = GCore.Pixels(GCore.DEFAULT_ROW_HEIGHT.num * 2),
                panels = [
                    GCommon.BarChart(
                        title = 'QTYPE for most popular Undelegated TLDs queried',
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
                                tickmargin = 90,
                            ),
                        ),
                        autotrace = True,
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'QtypeUndelegatedTld' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                      notEmpty(QType) ? QType : concat('TYPE', toString(QueryType)) AS DisplayQType,
                                      sum(Cnt) / ($to - $from) AS TldCnt,
                                      empty(Tld) ? '"."' : (isValidUTF8(Tld) ? Tld : base64Encode(Tld)) AS DisplayTld
                                  FROM
                                  (
                                      SELECT
                                          Tld,
                                          QueryType,
                                          sum(Cnt) AS Cnt,
                                          any(TotalCnt) AS TotalCnt
                                      FROM
                                      (
                                          SELECT
                                              Tld,
                                              sum(toUInt64(Count)) AS TotalCnt
                                          FROM $table
                                          WHERE
                                              $timeFilter
                                              AND NodeID IN {nodesel}
                                          GROUP BY Tld
                                          ORDER BY TotalCnt DESC, Tld ASC
                                          LIMIT 40
                                      ) AS TldCount
                                      ALL LEFT JOIN
                                      (
                                          SELECT
                                              Tld,
                                              QueryType,
                                              sum(toUInt64(Count)) AS Cnt
                                          FROM $table
                                          WHERE
                                              $timeFilter
                                              AND NodeID IN {nodesel}
                                          GROUP BY
                                              Tld,
                                              QueryType
                                          UNION ALL
                                          (
                                              SELECT
                                                  Tld,
                                                  QueryType,
                                                  CAST(0 AS UInt64) AS Cnt
                                              FROM
                                              (
                                                  SELECT
                                                      0 AS Zero,
                                                      Tld
                                                  FROM $table
                                                  WHERE
                                                      $timeFilter
                                                      AND NodeID IN {nodesel}
                                                  GROUP BY Tld
                                              ) AS ZeroTld
                                              ALL LEFT JOIN
                                              (
                                                  SELECT
                                                      0 AS Zero,
                                                      QueryType
                                                  FROM $table
                                                  WHERE
                                                      $timeFilter
                                                      AND NodeID IN {nodesel}
                                                  GROUP BY QueryType
                                              ) AS ZeroTYpe USING Zero
                                          )
                                      ) AS TldQTypeCounts USING Tld
                                      GROUP BY
                                          Tld,
                                          QueryType
                                  ) AS TldQTypeCountsTotal
                                  ALL INNER JOIN
                                  (
                                      SELECT
                                          value_name AS QType,
                                          toUInt16(value) AS QueryType
                                      FROM {nodeinfo_database}.iana_text
                                      WHERE registry_name = 'QTYPE'
                                  ) AS QTypeName USING QueryType
                                  GROUP BY
                                      Tld,
                                      QueryType,
                                      QType
                                  ORDER BY
                                      sum(TotalCnt) ASC,
                                      DisplayQType,
                                      Tld DESC""".format(
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
