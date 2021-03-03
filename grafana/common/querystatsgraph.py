# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Query statistics graph common target

import textwrap

import grafanacommon as GCommon

def QPSTargetGroup(agginfo, field, nodesel):
    return GCommon.ClickHouseTarget(
        database = agginfo['database'],
        table = 'Queries' + agginfo['table_suffix'],
        round = agginfo['round'],
        query = textwrap.dedent("""\
          SELECT t, groupArray((Name, qc))
          FROM
          (
            SELECT
              t,Name,sum(cnt)/{interval_divisor} AS qc
            FROM
            (
              SELECT
                $timeSeries AS t,
                NodeID,
                sum(QueryCount) AS cnt
              FROM $table
              WHERE $timeFilter AND NodeID IN {nodesel}
              GROUP BY t,NodeID
              ORDER BY t,NodeID
            ) AS NodeCount
            ALL INNER JOIN
            (
              SELECT
                {field} AS Name,
                toUInt16(node_id) AS NodeID
              FROM {nodeinfo_database}.node_text
            ) AS NodeName USING NodeID
            GROUP BY t, Name
            ORDER BY t, Name
          )
          GROUP BY t
          ORDER BY t""".format(
              field=field,
              interval_divisor=agginfo['interval_divisor'],
              nodesel=nodesel,
              nodeinfo_database=agginfo['nodeinfo_database'])),
        refId = 'A'
    )
