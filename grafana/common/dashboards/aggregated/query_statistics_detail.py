# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Aggregation query statistics

import textwrap

import grafanalib.core as GCore

import querystatsgraph as qsg
import grafanacommon as GCommon

def by_node_row(agginfo, nodesel):
    return GCore.Row(
        panels = [
            GCommon.QPSGraph(
                title = 'Queries by node',
                targets = [ qsg.QPSTargetGroup(agginfo, 'name', nodesel) ],
            ),
        ]
    )

def busiest_node_rows(agginfo, nodesel):
    return [
        GCore.Row(
            height = GCore.Pixels(40),
            panels = [
                GCommon.HTMLPanel('grafana/common/active_disabled_nodes.html', transparent=True),
            ],
        ),
        GCore.Row(
            panels = [
                GCore.Table(
                    dataSource = 'Visualizer',
                    title = '30 highest traffic active nodes',
                    showHeader = True,
                    styles = [
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
                            table = 'Queries' + agginfo['table_suffix'],
                            format = GCore.TABLE_TARGET_FORMAT,
                            round = agginfo['round'],
                            query = textwrap.dedent("""\
                              SELECT name AS Name, QPS
                              FROM
                              (
                                SELECT
                                  NodeID,
                                  sum(toUInt64(QueryCount)) / ($to - $from) AS QPS
                                FROM $table
                                WHERE $timeFilter
                                  AND NodeID IN {nodesel}
                                GROUP BY NodeID
                              ) AS NodeCount
                              ALL INNER JOIN {nodeinfo_database}.node_text
                              ON NodeID=node_id
                              WHERE {active_node}
                              ORDER BY QPS DESC
                              LIMIT 30
                            """.format(
                                nodesel=nodesel,
                                active_node=GCommon.COND_ACTIVE_NODE,
                                nodeinfo_database=agginfo['nodeinfo_database'])),
                            refId = 'A'
                        )
                    ]
                ),
                GCore.Table(
                    dataSource = 'Visualizer',
                    title = '30 lowest traffic active nodes',
                    showHeader = True,
                    styles = [
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
                            table = 'Queries' + agginfo['table_suffix'],
                            format = GCore.TABLE_TARGET_FORMAT,
                            round = agginfo['round'],
                            query = textwrap.dedent("""\
                              SELECT name AS Name, QPS
                              FROM
                              (
                                SELECT
                                  NodeID,
                                  sum(toUInt64(QueryCount)) / ($to - $from) AS QPS
                                FROM $table
                                WHERE $timeFilter
                                  AND NodeID IN {nodesel}
                                GROUP BY NodeID
                              ) AS NodeCounts
                              ALL INNER JOIN {nodeinfo_database}.node_text
                              ON NodeID=node_id
                              WHERE {active_node}
                              ORDER BY QPS ASC
                              LIMIT 30
                            """.format(
                                    nodesel=nodesel,
                                    active_node=GCommon.COND_ACTIVE_NODE,
                                    nodeinfo_database=agginfo['nodeinfo_database'])),
                            refId = 'A'
                        )
                    ]
                ),
            ]
        ),
        GCore.Row(
            panels = [
                GCore.Table(
                    dataSource = 'Visualizer',
                    title = 'Active nodes, most recent traffic',
                    showHeader = True,
                    span = 4,
                    styles = [
                        GCore.ColumnStyle(
                            pattern = 'Latest',
                            alias = 'Latest data',
                            type = GCore.StringColumnStyleType(
                                preserveFormat=True,
                                sanitize=False,
                            )
                        ),
                    ],
                    targets = [
                        GCommon.ClickHouseTarget(
                            database = agginfo['database'],
                            table = 'Queries' + agginfo['table_suffix'],
                            format = GCore.TABLE_TARGET_FORMAT,
                            round = agginfo['round'],
                            query = textwrap.dedent("""\
                              SELECT
                                name AS Name,
                                max(DateTime) AS Latest
                              FROM $table
                              ALL INNER JOIN {nodeinfo_database}.node_text
                                ON NodeID=node_id
                              WHERE
                                NodeID IN {nodesel}
                                AND {active_node}
                                GROUP BY NodeID, name, flags
                              ORDER BY Latest ASC, Name ASC
                            """.format(
                                nodesel=nodesel,
                                active_node=GCommon.COND_ACTIVE_NODE,
                                nodeinfo_database=agginfo['nodeinfo_database'])),
                            refId = 'A'
                        )
                    ]
                ),
                GCore.Table(
                    dataSource = 'Visualizer',
                    title = 'Active nodes without traffic',
                    showHeader = True,
                    span = 4,
                    styles = [
                        GCore.ColumnStyle(
                            pattern = 'Latest',
                            alias = 'Latest data',
                            type = GCore.StringColumnStyleType(
                                preserveFormat=True,
                                sanitize=False,
                            )
                        ),
                    ],
                    targets = [
                        GCommon.ClickHouseTarget(
                            database = agginfo['database'],
                            table = 'Queries' + agginfo['table_suffix'],
                            format = GCore.TABLE_TARGET_FORMAT,
                            round = agginfo['round'],
                            query = textwrap.dedent("""\
                              SELECT
                                Name
                              FROM
                              (
                                SELECT
                                  name AS Name,
                                  node_id AS NodeID
                                FROM {nodeinfo_database}.node_text
                                LEFT OUTER JOIN
                                (
                                  SELECT
                                    1 AS Present,
                                    NodeID
                                  FROM $table
                                  WHERE
                                      NodeID IN {nodesel}
                                  GROUP BY NodeID
                                ) AS NodePresent USING NodeID
                                WHERE NodeID IN {nodesel}
                                  AND Present=0
                                  AND {active_node}
                              )
                              ORDER BY Name ASC
                            """.format(
                                nodesel=nodesel,
                                active_node=GCommon.COND_ACTIVE_NODE,
                                nodeinfo_database=agginfo['nodeinfo_database'])),
                            refId = 'A'
                        )
                    ]
                ),
                GCore.Table(
                    dataSource = 'Visualizer',
                    title = 'Disabled nodes',
                    showHeader = True,
                    span = 4,
                    styles = [
                        GCore.ColumnStyle(
                            pattern = 'Latest',
                            alias = 'Latest data',
                            type = GCore.StringColumnStyleType(
                                preserveFormat=True,
                                sanitize=False,
                            )
                        ),
                    ],
                    targets = [
                        GCommon.ClickHouseTarget(
                            database = agginfo['database'],
                            table = 'Queries' + agginfo['table_suffix'],
                            format = GCore.TABLE_TARGET_FORMAT,
                            round = agginfo['round'],
                            query = textwrap.dedent("""\
                              SELECT
                                Name,
                                Latest > 0 ? toString(Latest) : '' AS Latest
                              FROM
                              (
                                SELECT
                                  name AS Name,
                                  node_id AS NodeID,
                                  flags
                                FROM {nodeinfo_database}.node_text
                                WHERE NodeID IN {nodesel}
                                  AND NOT {active_node}
                              ) AS NodeFlags
                              LEFT OUTER JOIN
                              (
                                SELECT
                                  max(DateTime) AS Latest,
                                  NodeID
                                FROM $table
                                WHERE NodeID IN {nodesel}
                                GROUP BY NodeID
                              ) AS NodeLatest USING NodeID
                              ORDER BY Name ASC
                            """.format(
                                nodesel=nodesel,
                                active_node=GCommon.COND_ACTIVE_NODE,
                                nodeinfo_database=agginfo['nodeinfo_database'])),
                            refId = 'A'
                        )
                    ]
                ),
            ]
        )
    ]

def dash(myuid, agginfo, nodesel, **kwargs):
    return GCommon.Dashboard(
        title = 'Query statistics detail',
        tags = [
            agginfo['graph_tag']
        ],
        uid = myuid,
        rows = [
            GCore.Row(
                panels = [
                    GCommon.QPSGraph(
                        title = 'Queries by city',
                        targets = [ qsg.QPSTargetGroup(agginfo, 'city_name', nodesel) ],
                    ),
                    GCommon.QPSGraph(
                        title = 'Queries by instance',
                        targets = [ qsg.QPSTargetGroup(agginfo, 'instance_name', nodesel) ],
                    ),
                ]
            ),
        ]
    )
