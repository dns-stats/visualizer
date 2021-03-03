# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Aggregation rcodes

import textwrap

import grafanalib.core as GCore

import grafanacommon as GCommon

def dash(myuid, agginfo, nodesel, **kwargs):
    return GCommon.Dashboard(
        title = "Responses (RCODE)",
        tags = [
            agginfo['graph_tag']
        ],
        uid = myuid,
        rows = [
            GCore.Row(
                panels = [
                    GCommon.RPSGraph(
                        title = 'Replies by RCODE',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Responses' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT t, groupArray((DisplayRcode, qc))
                                  FROM
                                  (
                                    SELECT
                                      t,
                                      notEmpty(RRcode) ? RRcode : concat('RCODE', toString(ResponseRcode)) AS DisplayRcode,
                                      cnt/{interval_divisor} AS qc
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
                                    ) AS RcodeList
                                    ALL INNER JOIN
                                    (
                                      SELECT
                                        value_name AS RRcode,
                                        toUInt16(value) AS ResponseRcode
                                      FROM {nodeinfo_database}.iana_text
                                      WHERE registry_name = 'RCODE'
                                    ) AS RCodeText USING ResponseRcode
                                    GROUP BY t, ResponseRcode, RRcode, cnt
                                    ORDER BY t, DisplayRcode
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel,
                                      nodeinfo_database=agginfo['nodeinfo_database'])),
                                refId = 'A'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                height = GCore.Pixels(GCore.DEFAULT_ROW_HEIGHT.num * 2),
                panels = [
                    GCommon.BarChart(
                        title = 'Reply Lengths by Rcode (< 1000 bytes)',
                        orientation = GCommon.BAR_CHART_ORIENTATION_VERTICAL,
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = True,
                            xaxis = GCommon.BarChartAxis(
                                title = 'Length in Bytes',
                            ),
                            yaxis = GCommon.BarChartAxis(
                                title = 'Queries per Second',
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_LINEAR,
                                tickmargin = 90,
                            ),
                        ),
                        autotrace = True,
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'RcodeResponseLength' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    notEmpty(RcodeText) ? RcodeText : concat('RCODE', toString(Rcode)) AS DisplayRcode,
                                    Len,
                                    Cnt / ($to - $from)
                                  FROM
                                  (
                                    SELECT
                                      Length as Len,
                                      Rcode,
                                      sum(Count) as Cnt
                                    FROM $table
                                    WHERE $timeFilter and Len < 1000
                                    AND NodeID IN {nodesel}
                                    GROUP BY Rcode, Len
                                  ) AS RCodeList
                                  LEFT JOIN
                                  (
                                    SELECT
                                      value_name as RcodeText,
                                      toUInt16(value) as Rcode
                                    FROM {nodeinfo_database}.iana_text
                                    WHERE registry_name = 'RCODE'
                                  ) AS RCodeText USING Rcode
                                  ORDER BY DisplayRcode, Len""".format(
                                      nodesel=nodesel,
                                      nodeinfo_database=agginfo['nodeinfo_database'])),
                                refId = 'A'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                height = GCore.Pixels(GCore.DEFAULT_ROW_HEIGHT.num * 2),
                panels = [
                    GCommon.BarChart(
                        title = 'Reply Lengths by Rcode (>= 1000 bytes)',
                        orientation = GCommon.BAR_CHART_ORIENTATION_VERTICAL,
                        layout = GCommon.BarChartLayout(
                            barmode = GCommon.BAR_CHART_LAYOUT_MODE_STACK,
                            showlegend = True,
                            xaxis = GCommon.BarChartAxis(
                                title = 'Length in Bytes',
                            ),
                            yaxis = GCommon.BarChartAxis(
                                title = 'Queries per Second',
                                axtype = GCommon.BAR_CHART_AXIS_TYPE_LINEAR,
                                tickmargin = 90,
                            ),
                        ),
                        autotrace = True,
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'RcodeResponseLength' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    notEmpty(RcodeText) ? RcodeText : concat('RCODE', toString(Rcode)) AS DisplayRcode,
                                    Len,
                                    Cnt / ($to - $from)
                                  FROM
                                  (
                                    SELECT
                                      Length as Len,
                                      Rcode,
                                      sum(Count) as Cnt
                                    FROM $table
                                    WHERE $timeFilter and Len >= 1000
                                    AND NodeID IN {nodesel}
                                    GROUP BY Rcode, Len
                                  ) AS RCodeList
                                  LEFT JOIN
                                  (
                                    SELECT
                                      value_name as RcodeText,
                                      toUInt16(value) as Rcode
                                    FROM {nodeinfo_database}.iana_text
                                    WHERE registry_name = 'RCODE'
                                  ) AS RCodeText USING Rcode
                                  ORDER BY DisplayRcode, Len""".format(
                                      nodesel=nodesel,
                                      nodeinfo_database=agginfo['nodeinfo_database'])),
                                refId = 'A'
                            ),
                        ],
                    ),
                ],
            ),
        ]
    )
