#!/usr/bin/env python3
#
# Copyright 2020 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Download geographic location data and update the Postgres table.
#
# Usage: dsv-geo-update [-n]

import csv
import io
import zipfile

import psycopg2
import requests

description = 'Download geographic location data and update postgresql'

def download_zip(url):
    response = requests.get(url)
    return zipfile.ZipFile(io.BytesIO(response.content))

def zip_contents(zipf, verbose):
    for zipinfo in zipf.infolist():
        if verbose:
            print('Processing {}'.format(zipinfo.filename))
        with zipf.open(zipinfo) as thefile:
            yield zipinfo.filename, thefile

def read_block_info(f, locdata):
    reader = csv.reader(io.TextIOWrapper(f, 'utf-8'))
    for row in reader:
        if row[0] != 'network':
            # Not all records have a geo ID and lat/long.
            if not row[1] or not row[7] or not row[8]:
                continue

            geo_id = int(row[1])
            country_id = int(row[2]) if row[2] else 0
            lat = float(row[7])
            long = float(row[8])
            if geo_id not in locdata:
                locdata[geo_id] = {'country_id': country_id, 'name': '', 'lat': lat, 'long': long}
            else:
                locdata[geo_id]['country_id'] = country_id
                locdata[geo_id]['lat'] = lat
                locdata[geo_id]['long'] = long

def read_location_info(f, locdata):
    reader = csv.reader(io.TextIOWrapper(f, 'utf-8'))
    for row in reader:
        if row[0] != 'geoname_id':
            geo_id = int(row[0])
            name = row[10]       # City name
            if not name:
                name = row[9]    # Subdivision 2 name
            if not name:
                name = row[7]    # Subdivision 1 name
            if not name:
                name = row[5]    # Country name
            if not name:
                name = row[3]    # Continent name
            if id not in locdata:
                locdata[geo_id] = {'country_id': 0, 'name': name, 'lat': 0.0, 'long': 0.0}
            else:
                locdata[geo_id]['name'] = name

def add_args(parser):
    parser.add_argument('-n', '--dry-run',
                        dest='dryrun', action='store_true', default=False,
                        help="show data updates but don't update database")
    parser.add_argument('-v', '--verbose',
                        action='store_true', default=False,
                        help='enable verbosity')
    parser.add_argument('--zipfile', default=None,
                        help='path to MaxMind GeoLite2-City-CSV.zip file, '
                             'file will be downloaded if omitted',
                        metavar='ZIPFILE')

def main(args, cfg):
    conn = None
    locdata = {}
    try:
        if args.zipfile:
            zipf = zipfile.ZipFile(args.zipfile)
        else:
            url = cfg['geo']['url'].format(licencekey=cfg['geo']['licencekey'])
            if args.verbose:
                print('Downloading {}'.format(url))
            zipf = download_zip(url)
        for fname, f in zip_contents(zipf, args.verbose):
            if fname.endswith('Locations-en.csv'):
                read_location_info(f, locdata)
            elif fname.endswith('Blocks-IPv4.csv') or fname.endswith('Blocks-IPv4.csv'):
                read_block_info(f, locdata)

        if args.dryrun:
            for geo_id, vals in locdata.items():
                print('{}: {}, ({}, {})'.format(
                    geo_id, vals['name'], vals['lat'], vals['long']))
        else:
            pgcfg = cfg['postgres']
            conn = psycopg2.connect(host=pgcfg['host'],
                                    dbname=pgcfg['database'],
                                    user=pgcfg['user'],
                                    password=pgcfg['password'])
            with conn.cursor() as cur:
                for geo_id, vals in locdata.items():
                    cur.execute('INSERT INTO geolocation '
                                '(id, country_id, name, latitude, longitude) '
                                'VALUES (%s, %s, %s, %s, %s) '
                                'ON CONFLICT (id) DO '
                                'UPDATE SET country_id=%s, name=%s, latitude=%s, longitude=%s',
                                (geo_id,
                                 vals['country_id'], vals['name'], vals['lat'], vals['long'],
                                 vals['country_id'], vals['name'], vals['lat'], vals['long']))
            conn.commit()
            conn.close()
        return 0
    except Exception:
        if conn is not None:
            conn.rollback()
            conn.close()
        raise
