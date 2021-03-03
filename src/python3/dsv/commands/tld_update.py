#!/usr/bin/env python3
#
# Copyright 2018-2020 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Update the list of top level domains. Uses the list of TLDs published
# by IANA at https://data.iana.org/TLD/tlds-alpha-by-domain.txt and
# checks individual TLDs using the IANA TLD page at
# https://www.iana.org/domains/root/db/<tld>.html.
#
# Usage: dsv-tld-update

import logging
import urllib.request
import encodings.idna
import sys

import psycopg2

description = 'Update the list of top level domains'

def read_url(url, encoding='utf-8'):
    with urllib.request.urlopen(url) as page:
        return page.read().decode(encoding)

def tld_type(tld, tldurlfmt):
    # Legacy TLD are all in the base set. New ones will be either
    # ccTLD or New-gTLD. New ccTLDs are either (a) any 2 character TLD,
    # or (b) an IDN flagged as a ccTLD. To determine the latter,
    # check the IANA TLD page and look for the text
    # 'Country-code top-level domain'.
    if len(tld) == 2 or \
       (tld.startswith('xn--') and \
        read_url(tldurlfmt.format(tld)).find('Country-code top-level domain') != -1):
        return 'ccTLD'
    return 'New-gTLD'

def add_args(parser):
    parser.add_argument('-n', '--dry-run',
                        dest='dryrun', action='store_true', default=False,
                        help='perform a trial run')
    parser.add_argument('-v', '--verbose',
                        action='store_true', default=False,
                        help='enable verbosity')

def main(args, cfg):
    conn = None
    tlds = set()
    pg_tlds = set()
    try:
        # pylint: disable=no-member
        if args.verbose and not sys.stdout.encoding.lower().startswith('utf'):
            print('Output path is not Unicode. U-Labels will not display correctly.')

        for line in read_url(cfg['urls']['tldlist'], 'ascii').splitlines():
            tld = line.split('#')[0].strip().lower()
            if tld:
                tlds.add(tld)

        pgcfg = cfg['postgres']
        conn = psycopg2.connect(host=pgcfg['host'],
                                dbname=pgcfg['database'],
                                user=pgcfg['user'],
                                password=pgcfg['password'])

        with conn.cursor() as cur:
            cur.execute('SELECT name FROM tld')
            pg_tlds_tuples = cur.fetchall()
            for pg_tlds_tuple in pg_tlds_tuples:
                pg_tlds.add(pg_tlds_tuple[0])

            to_remove = pg_tlds - tlds
            to_add = tlds - pg_tlds

            # Historically the tld table had no ulabel column so do a
            # quick check to ensure this is populated for every tld.
            for tld in sorted(pg_tlds):
                ulabel = encodings.idna.ToUnicode(tld)
                msg = 'Update TLD {tld} U-Label {ulabel}'.format(tld=tld, ulabel=ulabel)
                logging.info(msg)
                if args.verbose:
                    print(msg)
                if not args.dryrun:
                    cur.execute('UPDATE tld SET ulabel = %s '
                                'WHERE name = %s AND ulabel IS null',
                                (ulabel, tld))

            for tld in sorted(to_add):
                tldtype = tld_type(tld, cfg['urls']['tldpage'])
                ulabel = encodings.idna.ToUnicode(tld)
                msg = 'Adding TLD {tld} U-Label {ulabel} ({tldtype})'.format(
                    tld=tld, ulabel=ulabel, tldtype=tldtype)
                logging.info(msg)
                if args.verbose:
                    print(msg)
                if not args.dryrun:
                    cur.execute('INSERT INTO tld (name, ulabel, type_id) '
                                'SELECT %s, %s, id FROM tld_type WHERE name=%s',
                                (tld, ulabel, tldtype))

            for tld in sorted(to_remove):
                msg = 'Removing TLD {tld}'.format(tld=tld)
                logging.info(msg)
                if args.verbose:
                    print(msg)
                if not args.dryrun:
                    cur.execute('DELETE FROM tld WHERE name = %s', (tld,))

            conn.commit()
        conn.close()
        return 0
    except psycopg2.Error:
        if conn is not None:
            conn.rollback()
            conn.close()
        raise
