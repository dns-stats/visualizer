# Copyright 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Aggregation geolocation city

import textwrap

import grafanalib.core as GCore

import grafanacommon as GCommon

def busiest_city_row(agginfo, nodesel):
    return GCore.Row(
        panels = [
            GCore.Table(
                dataSource = 'Visualizer',
                title = '25 busiest client traffic locations',
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
                        table = 'ClientGeoLocations' + agginfo['table_suffix'],
                        format = GCore.TABLE_TARGET_FORMAT,
                        round = agginfo['round'],
                        query = textwrap.dedent("""\
                          SELECT
                              name AS City,
                              total / ($to - $from) AS QPS
                          FROM
                          (
                              SELECT
                                  ClientGeoLocation as city_id,
                                  sum(toUInt64(Count)) AS total
                              FROM $table
                              WHERE $timeFilter
                                  AND NodeID IN {nodesel}
                                  AND city_id != 0
                              GROUP BY city_id
                          )
                          LEFT JOIN
                          (
                              SELECT
                                  id,
                                  name
                              FROM {nodeinfo_database}.geolocation
                          ) AS GeoName ON id = toUInt64(city_id)
                          GROUP BY name, total
                          ORDER BY total DESC
                          LIMIT 25""".format(
                            interval_divisor=agginfo['interval_divisor'],
                            nodesel=nodesel,
                            nodeinfo_database=agginfo['nodeinfo_database'])),
                        refId = 'A'
                    )
                ]
            ),
            GCommon.HTMLPanel('grafana/common/city_country.html', transparent=True),
        ]
    )

def dash(myuid, agginfo, nodesel, **kwargs):
    return GCommon.Dashboard(
        title = "Client Geographic Locations - City",
        tags = [
            agginfo['graph_tag']
        ],
        uid = myuid,
        rows = [
            GCore.Row(
                height = GCore.Pixels(GCore.DEFAULT_ROW_HEIGHT.num * 3),
                panels = [
                    GCommon.WorldMap(
                        title = 'Client Locations by City',
                        locationData = 'table',
                        geohashField = 'loc',
                        labelField = 'city',
                        latitudeField = 'latitude',
                        longitudeField = 'longitude',
                        metricField = 'cnt',
                        queryType = 'coordinates',
                        valueName = 'current',
                        targets = [
                            GCommon.ClickHouseTableTarget(
                                database = agginfo['database'],
                                table = 'ClientGeoLocations' + agginfo['table_suffix'],
                                round = agginfo['round'],
                                query = textwrap.dedent("""\
                                    SELECT
                                        name AS city,
                                        latitude,
                                        longitude,
                                        total / ($to - $from) AS cnt
                                    FROM
                                    (
                                        SELECT
                                            ClientGeoLocation,
                                            sum(toUInt64(Count)) AS total
                                        FROM $table
                                        WHERE $timeFilter
                                            AND NodeID IN {nodesel}
                                            AND ClientGeoLocation != 0
                                        GROUP BY ClientGeoLocation
                                    ) AS LocTotals
                                    LEFT JOIN
                                    (
                                        SELECT
                                            id,
                                            name,
                                            latitude,
                                            longitude
                                        FROM {nodeinfo_database}.geolocation
                                    ) AS GeoNameLoc ON id = toUInt64(ClientGeoLocation)
                                    GROUP BY name, latitude, longitude, total
                                    """.format(
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
