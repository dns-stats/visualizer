# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Aggregation query attributes

import textwrap

import grafanalib.core as GCore

import grafanacommon as GCommon

def dash(myuid, agginfo, nodesel, **kwargs):
    return GCommon.Dashboard(
        title = "Query types (QTYPE)",
        tags = [
            agginfo['graph_tag']
        ],
        uid = myuid,
        rows = [
            GCore.Row(
                panels = [
                    GCommon.QPSGraph(
                        title = 'Queries by main QTYPEs',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Queries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT t, groupArray((DisplayQType, qc)) AS QTypeCount
                                  FROM
                                  (
                                    SELECT
                                      t,
                                      notEmpty(QType) ? QType : concat('TYPE', toString(QueryType)) AS DisplayQType,
                                      cnt/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        QueryTypeMap.QueryType AS QueryType,
                                        sum(toUInt64(QueryTypeMap.Count)) AS cnt
                                      FROM $table
                                      ARRAY JOIN QueryTypeMap
                                      WHERE $timeFilter
                                        AND QueryType IN (1,2,5,6,12,15,28,33,38,255)
                                        AND NodeID IN {nodesel}
                                      GROUP BY t, QueryType
                                      ORDER BY t, QueryType
                                    ) AS QTypeCount
                                    ALL INNER JOIN
                                    (
                                      SELECT
                                        value_name AS QType,
                                        toUInt16(value) AS QueryType
                                      FROM {nodeinfo_database}.iana_text
                                      WHERE registry_name = 'QTYPE'
                                    ) AS QTypeName USING QueryType
                                    GROUP BY t, QueryType, QType, cnt
                                    ORDER BY t, DisplayQType
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
                    GCommon.QPSGraph(
                        title = 'DNSSEC Queries by QTYPE',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Queries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT t, groupArray((DisplayQType, qc)) AS QTypeCount
                                  FROM
                                  (
                                    SELECT
                                      t,
                                      notEmpty(QType) ? QType : concat('TYPE', toString(QueryType)) AS DisplayQType,
                                      cnt/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        QueryTypeMap.QueryType AS QueryType,
                                        sum(toUInt64(QueryTypeMap.Count)) AS cnt
                                      FROM $table
                                      ARRAY JOIN QueryTypeMap
                                      WHERE $timeFilter
                                        AND QueryType IN
                                        (
                                          SELECT toUInt16(value)
                                          FROM {nodeinfo_database}.iana_text
                                          WHERE registry_name = 'DNSSEC QTYPE'
                                        )
                                        AND NodeID IN {nodesel}
                                      GROUP BY t, QueryType
                                      ORDER BY t, QueryType
                                    ) AS QTypeCount
                                    ALL INNER JOIN
                                    (
                                      SELECT
                                        value_name AS QType,
                                        toUInt16(value) AS QueryType
                                      FROM {nodeinfo_database}.iana_text
                                      WHERE registry_name = 'DNSSEC QTYPE'
                                    ) AS QTypeName USING QueryType
                                    GROUP BY t, QueryType, QType, cnt
                                    ORDER BY t, DisplayQType
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
                panels = [
                    GCommon.QPSGraph(
                        title = 'Queries by all QTYPEs',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Queries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT t, groupArray((DisplayQType, qc)) AS QTypeCount
                                  FROM
                                  (
                                    SELECT
                                      t,
                                      notEmpty(QType) ? QType : concat('TYPE', toString(QueryType)) AS DisplayQType,
                                      cnt/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        QueryTypeMap.QueryType AS QueryType,
                                        sum(toUInt64(QueryTypeMap.Count)) AS cnt
                                      FROM $table
                                      ARRAY JOIN QueryTypeMap
                                      WHERE $timeFilter AND NodeID IN {nodesel}
                                      GROUP BY t, QueryType
                                      ORDER BY t, QueryType
                                    ) AS QTypeCount
                                    ALL INNER JOIN
                                    (
                                      SELECT
                                        value_name AS QType,
                                        toUInt16(value) AS QueryType
                                      FROM {nodeinfo_database}.iana_text
                                      WHERE registry_name = 'QTYPE'
                                    ) AS QTypeName USING QueryType
                                    GROUP BY t, QueryType, QType, cnt
                                    ORDER BY t, DisplayQType
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
                    GCommon.QPSGraph(
                        title = 'Popular query names by QTYPE',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QtypePopularQueryNames' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT t, groupArray((QNameType, qc)) AS QNameTypeCount
                                  FROM
                                  (
                                    SELECT
                                      t,
                                      concat(PopularQueryName, ':', notEmpty(QType) ? QType : concat('TYPE', toString(QueryType))) AS QNameType,
                                      cnt/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        PopularQueryName,
                                        QueryType,
                                        sum(toUInt64(Count)) AS cnt
                                      FROM $table
                                      WHERE $timeFilter AND NodeID IN {nodesel}
                                      GROUP BY t, PopularQueryName, QueryType
                                      ORDER BY t, PopularQueryName, QueryType
                                    ) AS QTypeCount
                                    ALL INNER JOIN
                                    (
                                      SELECT
                                        value_name AS QType,
                                        toUInt16(value) AS QueryType
                                      FROM {nodeinfo_database}.iana_text
                                      WHERE registry_name = 'QTYPE'
                                    ) AS QTypeName USING QueryType
                                    GROUP BY t, PopularQueryName, QueryType, QType, cnt
                                    ORDER BY t, PopularQueryName, QType
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
                panels = [
                    GCommon.BarChart(
                        title = 'Query name lengths showing QTYPE',
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
                                table = 'QtypeQueryNameLength' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    notEmpty(QType) ? QType : concat('TYPE', toString(QueryType)) AS DisplayQType,
                                    Len,
                                    Cnt / ($to - $from)
                                  FROM
                                  (
                                    SELECT
                                      QueryNameLength AS Len,
                                      QueryType,
                                      sum(Count) AS Cnt
                                    FROM $table
                                    WHERE $timeFilter
                                    AND NodeID IN {nodesel}
                                    GROUP BY QueryType, Len
                                  ) AS QTypeCount
                                  ALL INNER JOIN
                                  (
                                    SELECT
                                      value_name AS QType,
                                      toUInt16(value) AS QueryType
                                    FROM {nodeinfo_database}.iana_text
                                    WHERE registry_name = 'QTYPE'
                                  ) AS QTypeName USING QueryType
                                  ORDER BY DisplayQType, Len""".format(
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
