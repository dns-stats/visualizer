# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Aggregation server IP address plots

import textwrap

import grafanalib.core as GCore

import grafanacommon as GCommon

def dash(myuid, agginfo, nodesel, **kwargs):
    return GCommon.Dashboard(
        title = "Server IP address",
        tags = [
            agginfo['graph_tag']
        ],
        uid = myuid,
        rows = [
            GCore.Row(
                panels = [
                    GCommon.QPSGraph(
                        title = 'Server IP address',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'ServerAddressTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT t, groupArray((replaceRegexpOne(Addr, '^::ffff:', ''), qc)) AS AddrCount
                                  FROM
                                  (
                                    SELECT
                                      t,Addr,cnt/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        IPv6NumToString(ServerAddress) AS Addr,
                                        sum(toUInt64(Count)) AS cnt
                                      FROM $table
                                      WHERE $timeFilter
                                        AND NodeID IN {nodesel}
                                        AND ServerAddress IN (
                                          SELECT IPv6StringToNum(address)
                                          FROM {nodeinfo_database}.server_address )
                                      GROUP BY t, Addr
                                      ORDER BY t, Addr
                                    )
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
                        title = 'Server IP address, UDP',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'ServerAddressTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT t, groupArray((replaceRegexpOne(Addr, '^::ffff:', ''), qc)) AS AddrCount
                                  FROM
                                  (
                                    SELECT
                                      t,Addr,cnt/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        IPv6NumToString(ServerAddress) AS Addr,
                                        sum(toUInt64(Count)) AS cnt
                                      FROM $table
                                      WHERE $timeFilter
                                        AND TransportTCP = 0
                                        AND NodeID IN {nodesel}
                                        AND ServerAddress IN (
                                          SELECT IPv6StringToNum(address)
                                          FROM {nodeinfo_database}.server_address )
                                      GROUP BY t, Addr
                                      ORDER BY t, Addr
                                    )
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
                        title = 'Server IP address, TCP',
                        targets = [
                            GCommon.ClickHouseTarget(
                                database = agginfo['database'],
                                table = 'ServerAddressTransport' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                  SELECT t, groupArray((replaceRegexpOne(Addr, '^::ffff:', ''), qc)) AS AddrCount
                                  FROM
                                  (
                                    SELECT
                                      t,Addr,cnt/{interval_divisor} AS qc
                                    FROM
                                    (
                                      SELECT
                                        $timeSeries AS t,
                                        IPv6NumToString(ServerAddress) AS Addr,
                                        sum(toUInt64(Count)) AS cnt
                                      FROM $table
                                      WHERE $timeFilter
                                        AND TransportTCP = 1
                                        AND NodeID IN {nodesel}
                                        AND ServerAddress IN (
                                          SELECT IPv6StringToNum(address)
                                          FROM {nodeinfo_database}.server_address )
                                      GROUP BY t, Addr
                                      ORDER BY t, Addr
                                    )
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
        ]
    )
