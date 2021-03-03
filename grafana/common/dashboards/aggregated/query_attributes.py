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
        title = "Query attributes",
        tags = [
            agginfo['graph_tag']
        ],
        uid = myuid,
        rows = [
            GCore.Row(
                panels = [
                    GCommon.QPSGraph(
                        title = 'Queries by DO',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Queries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(QueryDOCount))/{interval_divisor} AS DO
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
                                    sum(toUInt64(QueryCount - QueryDOCount))/{interval_divisor} AS NotDO
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
                        title = 'Queries by OPCODE',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Queries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT t, groupArray((DisplayQOpcode, qc))
                                  FROM
                                  (
                                    SELECT
                                      t,
                                      notEmpty(QOpcode) ? QOpcode : concat('OPCODE', toString(QueryOpcode)) AS DisplayQOpcode,
                                      sum(cnt)/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        QueryOpcodeMap.QueryOpcode AS QueryOpcode,
                                        sum(toUInt64(QueryOpcodeMap.Count)) AS cnt
                                      FROM $table
                                      ARRAY JOIN QueryOpcodeMap
                                      WHERE $timeFilter AND NodeID IN {nodesel}
                                      GROUP BY t, QueryOpcode
                                      ORDER BY t, QueryOpcode
                                    ) AS QOpcodeCounts
                                    ALL INNER JOIN
                                    (
                                      SELECT
                                        value_name AS QOpcode,
                                        toUInt8(value) AS QueryOpcode
                                      FROM {nodeinfo_database}.iana_text
                                      WHERE registry_name = 'OPCODE'
                                    ) AS QOpcodeName USING QueryOpcode
                                    GROUP BY t, QueryOpcode, QOpcode
                                    ORDER BY t, DisplayQOpcode
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
                        title = 'Queries by RD',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'Queries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(QueryRecursionDesiredCount))/{interval_divisor} AS RD
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
                        ],
                    ),
                    GCommon.QPSGraph(
                        title = 'Queries with IDN QNAMEs',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'IDNQueryCount' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(Count))/{interval_divisor} AS IDN
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
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.QPSGraph(
                        title = 'Queries by EDNS Version',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'EDNSQueries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    t,
                                    groupArray((concat('EDNS', toString(EDNSVersion)), qc))
                                  FROM
                                  (
                                    SELECT
                                      t,
                                      EDNSVersion,
                                      sum(cnt)/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        EDNSQueryMap.EDNSVersion AS EDNSVersion,
                                        sum(toUInt64(EDNSQueryMap.EDNSCount)) AS cnt
                                      FROM $table
                                      ARRAY JOIN EDNSQueryMap
                                      WHERE
                                        $timeFilter
                                        AND NodeID IN {nodesel}
                                      GROUP BY
                                        t,
                                        EDNSVersion
                                      ORDER BY
                                        t,
                                        EDNSVersion
                                    )
                                    GROUP BY
                                      t,
                                      EDNSVersion
                                    ORDER BY
                                      t,
                                      EDNSVersion
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'A'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'EDNSQueries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(NonEDNSQueryCount))/{interval_divisor} AS NonEDNS
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                    AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'B'
                            ),
                        ],
                    ),
                    GCommon.QPSGraph(
                        title = 'CHAOS Queries',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'CHQueries' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    t,
                                    groupArray((concat(CHQTypeName, ':', CHQName), qc))
                                  FROM
                                  (
                                    SELECT
                                      t,
                                      CHQTypeName,
                                      CHQName,
                                      sum(cnt)/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        CHQType,
                                        CHQName AS CHQName,
                                        sum(toUInt64(CHCount)) AS cnt
                                      FROM $table
                                      WHERE
                                        $timeFilter
                                        AND NodeID IN {nodesel}
                                      GROUP BY
                                        t,
                                        CHQType,
                                        CHQName
                                      ORDER BY
                                        t
                                    ) AS CHQTypeCounts
                                    ALL INNER JOIN
                                    (
                                      SELECT
                                        value_name AS CHQTypeName,
                                        toUInt16(value) AS CHQType
                                      FROM {nodeinfo_database}.iana_text
                                      WHERE registry_name = 'QTYPE'
                                    ) AS CHQTypeName USING CHQType
                                    GROUP BY
                                      t,
                                      CHQType,
                                      CHQTypeName,
                                      CHQName
                                    ORDER BY
                                      t,
                                      CHQTypeName ASC,
                                      CHQName ASC
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
                        title = 'Queries by classification',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(AForACount))/{interval_divisor} AS AForA
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
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(AForRootCount))/{interval_divisor} AS AForRoot
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                    AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'B'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(FunnyQueryClassCount))/{interval_divisor} AS FunnyQueryClass
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                    AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'C'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(FunnyQueryTypeCount))/{interval_divisor} AS FunnyQueryType
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                    AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'D'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(LocalhostCount))/{interval_divisor} AS Localhost
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                    AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'E'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(NonAuthTldCount))/{interval_divisor} AS NonAuthTld
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                    AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'F'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(Count -
                                      (AForACount +
                                       AForRootCount +
                                       FunnyQueryClassCount +
                                       FunnyQueryTypeCount +
                                       LocalhostCount +
                                       NonAuthTldCount +
                                       RFC1918PtrCount +
                                       RootServersNetCount +
                                       SrcPortZeroCount
                                      )))/{interval_divisor} AS OK
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                    AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'G'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(RFC1918PtrCount))/{interval_divisor} AS RFC1918Ptr
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                    AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'H'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(RootServersNetCount))/{interval_divisor} AS RootServersNet
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                    AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'I'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    sum(toUInt64(SrcPortZeroCount))/{interval_divisor} AS SrcPortZero
                                  FROM $table
                                  WHERE
                                    $timeFilter
                                    AND NodeID IN {nodesel}
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'J'
                            ),
                        ],
                    ),
                ],
            ),
            GCore.Row(
                panels = [
                    GCommon.QPSGraph(
                        title = 'Count of client fixed subnets sending each query classification',
                        yAxes = GCore.single_y_axis(
                            format = GCore.SHORT_FORMAT,
                            label = 'Distinct client fixed subnets every {}'.format(agginfo['description']),
                        ),
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    avg(PrefixCount) AS AForA
                                  FROM
                                  (
                                    SELECT
                                      DateTime,
                                      uniqExact(FixedPrefix) AS PrefixCount
                                    FROM $table
                                    WHERE
                                      $timeFilter
                                      AND NodeID IN {nodesel}
                                      AND AForACount > 0
                                    GROUP BY DateTime
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      nodesel=nodesel)),
                                refId = 'A'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    avg(PrefixCount) AS AForRoot
                                  FROM
                                  (
                                    SELECT
                                      DateTime,
                                      uniqExact(FixedPrefix) AS PrefixCount
                                    FROM $table
                                    WHERE
                                      $timeFilter
                                      AND NodeID IN {nodesel}
                                      AND AForRootCount > 0
                                    GROUP BY DateTime
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      nodesel=nodesel)),
                                refId = 'B'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    avg(PrefixCount) AS FunnyQueryClass
                                  FROM
                                  (
                                    SELECT
                                      DateTime,
                                      uniqExact(FixedPrefix) AS PrefixCount
                                    FROM $table
                                    WHERE
                                      $timeFilter
                                      AND NodeID IN {nodesel}
                                      AND FunnyQueryClassCount > 0
                                    GROUP BY DateTime
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      nodesel=nodesel)),
                                refId = 'C'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    avg(PrefixCount) AS FunnyQueryType
                                  FROM
                                  (
                                    SELECT
                                      DateTime,
                                      uniqExact(FixedPrefix) AS PrefixCount
                                    FROM $table
                                    WHERE
                                      $timeFilter
                                      AND NodeID IN {nodesel}
                                      AND FunnyQueryTypeCount > 0
                                    GROUP BY DateTime
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      nodesel=nodesel)),
                                refId = 'D'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    avg(PrefixCount) AS Localhost
                                  FROM
                                  (
                                    SELECT
                                      DateTime,
                                      uniqExact(FixedPrefix) AS PrefixCount
                                    FROM $table
                                    WHERE
                                      $timeFilter
                                      AND NodeID IN {nodesel}
                                      AND LocalhostCount > 0
                                    GROUP BY DateTime
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'E'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    avg(PrefixCount) AS NonAuthTld
                                  FROM
                                  (
                                    SELECT
                                      DateTime,
                                      uniqExact(FixedPrefix) AS PrefixCount
                                    FROM $table
                                    WHERE
                                      $timeFilter
                                      AND NodeID IN {nodesel}
                                      AND NonAuthTldCount > 0
                                    GROUP BY DateTime
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      interval_divisor=agginfo['interval_divisor'],
                                      nodesel=nodesel)),
                                refId = 'F'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    avg(PrefixCount) AS OK
                                  FROM
                                  (
                                    SELECT
                                      DateTime,
                                      uniqExact(FixedPrefix) AS PrefixCount
                                    FROM $table
                                    WHERE
                                      $timeFilter
                                      AND NodeID IN {nodesel}
                                      AND Count >
                                            (AForACount +
                                             AForRootCount +
                                             FunnyQueryClassCount +
                                             FunnyQueryTypeCount +
                                             LocalhostCount +
                                             NonAuthTldCount +
                                             RFC1918PtrCount +
                                             RootServersNetCount +
                                             SrcPortZeroCount)
                                    GROUP BY DateTime
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      nodesel=nodesel)),
                                refId = 'G'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    avg(PrefixCount) AS RFC1918Ptr
                                  FROM
                                  (
                                    SELECT
                                      DateTime,
                                      uniqExact(FixedPrefix) AS PrefixCount
                                    FROM $table
                                    WHERE
                                      $timeFilter
                                      AND NodeID IN {nodesel}
                                      AND RFC1918PtrCount > 0
                                    GROUP BY DateTime
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      nodesel=nodesel)),
                                refId = 'H'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    avg(PrefixCount) AS RootServersNet
                                  FROM
                                  (
                                    SELECT
                                      DateTime,
                                      uniqExact(FixedPrefix) AS PrefixCount
                                    FROM $table
                                    WHERE
                                      $timeFilter
                                      AND NodeID IN {nodesel}
                                      AND RootServersNetCount > 0
                                    GROUP BY DateTime
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      nodesel=nodesel)),
                                refId = 'I'
                            ),
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'QueryClassifications' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT
                                    $timeSeries AS t,
                                    avg(PrefixCount) AS SrcPortZero
                                  FROM
                                  (
                                    SELECT
                                      DateTime,
                                      uniqExact(FixedPrefix) AS PrefixCount
                                    FROM $table
                                    WHERE
                                      $timeFilter
                                      AND NodeID IN {nodesel}
                                      AND SrcPortZeroCount > 0
                                    GROUP BY DateTime
                                  )
                                  GROUP BY t
                                  ORDER BY t""".format(
                                      nodesel=nodesel)),
                                refId = 'J'
                            ),
                        ],
                    ),
                ],
            ),
        ]
    )
