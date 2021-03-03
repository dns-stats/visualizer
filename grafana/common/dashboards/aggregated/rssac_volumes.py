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
        title = "RSSAC volumes",
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
                    GCommon.QPMGraph(
                        title = 'Queries and Responses',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toUInt64(QueryCount))/{interval_divisor} AS "TCP-IPv4-Queries",
                                    60 * sum(toUInt64(ResponseCount))/{interval_divisor} AS "TCP-IPv4-Responses"
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
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toUInt64(QueryCount))/{interval_divisor} AS "TCP-IPv6-Queries",
                                    60 * sum(toUInt64(ResponseCount))/{interval_divisor} AS "TCP-IPv6-Responses"
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
                                refId = 'B'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toUInt64(QueryCount))/{interval_divisor} AS "UDP-IPv4-Queries",
                                    60 * sum(toUInt64(ResponseCount))/{interval_divisor} AS "UDP-IPv4-Responses"
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
                                refId = 'C'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toUInt64(QueryCount))/{interval_divisor} AS "UDP-IPv6-Queries",
                                    60 * sum(toUInt64(ResponseCount))/{interval_divisor} AS "UDP-IPv6-Responses"
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
                                refId = 'D'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.QPMGraph(
                        title = 'Difference in query and response volume',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toInt64(QueryCount) - ResponseCount)/{interval_divisor} AS "TCP-IPv4-Difference"
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
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toUInt64(QueryCount) - ResponseCount)/{interval_divisor} AS "TCP-IPv6-Difference"
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
                                refId = 'B'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toInt64(QueryCount) - ResponseCount)/{interval_divisor} AS "UDP-IPv4-Difference"
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
                                refId = 'C'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryResponseTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    60 * sum(toInt64(QueryCount) - ResponseCount)/{interval_divisor} AS "UDP-IPv6-Difference"
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
                                refId = 'D'
                            ),
                        ],
                    ),
                ],
            ),
        ]
    )
