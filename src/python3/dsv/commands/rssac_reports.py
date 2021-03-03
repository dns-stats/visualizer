#!/usr/bin/env python3
#
# Copyright 2019-2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Generate RSSAC reports for the given date. Default to 7 days ago.

import argparse
import datetime
import logging
import pathlib
import random
import shutil
import ssl
import sys
import textwrap
import urllib.request

import clickhouse_driver
import clickhouse_driver.errors

description = 'generate RSSAC reports for the given day.'

DATE_FORMATS = ['%Y-%m-%d']

REPORTS = ['load-time', 'rcode-volume', 'traffic-sizes',
           'traffic-volume', 'unique-sources']

URL_FORMAT = '/render/d-solo/dsv-5minagg-rssac-report/' \
    'rssac-reporting?orgId=1&from={start:d}&to={end:d}&var-Server={server}&' \
    'panelId={panelid}&width=1000&height=600&tz=UTC&theme=light'

def read_date(arg):
    for date_fmt in DATE_FORMATS:
        try:
            return datetime.datetime.strptime(arg, date_fmt).date()
        except ValueError:
            pass
    raise ValueError('{0} is not a valid date'.format(arg))

def valid_date_type(arg):
    try:
        return read_date(arg)
    except ValueError as e:
        raise argparse.ArgumentTypeError(
            'Date {0} not valid. Expected format YYYY-MM-DD.'.format(arg)) from e

def yaml_header(report, service, date):
    return textwrap.dedent("""\
        ---
        version: rssac002v4
        service: {service}
        start-period: {date}T00:00:00Z
        metric: {report}
        """.format(
            report=report,
            service=service,
            date=date.strftime('%Y-%m-%d')))

def yaml_2colvalue(data):
    ok = True
    res = ''
    for row in data:
        res += '{}: {}\n'.format(row[0], row[1])
        ok = ok and (row[1] != '-')
    return (res, ok)

def yaml_3colvalue(data):
    ok = True
    name = None
    res = ''
    for row in data:
        if not name or name != row[0]:
            name = row[0]
            res += '{}:\n'.format(name)
        res += '  {}: {}\n'.format(row[1], row[2])
        ok = ok and (row[2] != '-')
    return (res, ok)

YAML_DATA = {
    'load-time': [(yaml_3colvalue,
                   textwrap.dedent("""\
                       SELECT
                           'time' AS Name,
                           Serial,
                           RSSACLatency == -1
                               ? '-'
                               : toString(RSSACLatency)
                               AS Latency
                       FROM
                       (
                           SELECT
                               Serial,
                               min(toInt32(Latency)) AS RSSACLatency
                           FROM dsv.ZoneLatency
                           WHERE Date='{date}'
                           AND PercentNodesUpdated >= {load_time_threshold}
                           AND NodeID IN
                           (
                               SELECT toUInt16(node_id)
                               FROM dsv.node_text
                               WHERE server_name='{server}'
                           )
                           GROUP BY Serial

                           UNION ALL

                           SELECT
                               Serial,
                               toInt32(-1) AS RSSACLatency
                           FROM
                           (
                               SELECT
                                 Serial,
                                 max(PercentNodesUpdated) AS MaxPercent
                               FROM dsv.ZoneLatency
                               WHERE Date='{date}'
                               AND NodeID IN
                               (
                                 SELECT toUInt16(node_id)
                                 FROM dsv.node_text
                                 WHERE server_name='{server}'
                               )
                               GROUP BY Serial
                           )
                           WHERE MaxPercent < {load_time_threshold}
                           GROUP BY Serial
                       )
                       GROUP BY Serial, RSSACLatency
                       ORDER BY Serial ASC
                    """))],
    'rcode-volume': [(yaml_2colvalue,
                      textwrap.dedent("""\
                          SELECT
                              Rcode,
                              cnt
                          FROM
                          (
                              SELECT
                                  ResponseRcodeMap.ResponseRcode AS Rcode,
                                  sum(toUInt64(ResponseRcodeMap.Count)) AS cnt
                              FROM dsv_five_minute.Responses
                              ARRAY JOIN ResponseRcodeMap
                              WHERE (Date = '{date}') AND (NodeID IN
                              (
                                  SELECT toUInt16(node_id)
                                  FROM dsv.node_text
                                  WHERE server_name='{server}'
                              ))
                              GROUP BY Rcode
                          )
                          GROUP BY Rcode, cnt
                          ORDER BY Rcode ASC
                       """))],
    'traffic-sizes': [(yaml_3colvalue,
                       textwrap.dedent("""\
                           SELECT
                               'udp-request-sizes' AS Name,
                               Len = 288 ? '288-' : concat(toString(Len), '-', toString(Len + 15))AS UDPQueryLen,
                               sum(Cnt) AS UDPQueryCnt
                           FROM
                           (
                               SELECT
                                   intDiv(QueryLengthMap.Length > 288 ? 288 : QueryLengthMap.Length, 16)*16 AS Len,
                                   sum(toUInt64(QueryLengthMap.Count)) AS Cnt
                               FROM dsv_five_minute.QueryResponseLength
                               ARRAY JOIN QueryLengthMap
                               WHERE Date='{date}'
                               AND TransportTCP=0
                               AND NodeID IN
                               (
                                  SELECT toUInt16(node_id)
                                  FROM dsv.node_text
                                  WHERE server_name='{server}'
                               )
                               GROUP BY Len
                           )
                           GROUP BY Name, Len
                           ORDER BY Len
                        """)),
                      (yaml_3colvalue,
                       textwrap.dedent("""\
                           SELECT
                               'udp-response-sizes' AS Name,
                               Len = 4096 ? '4096-' : concat(toString(Len), '-', toString(Len + 15))AS UDPResponseLen,
                               sum(Cnt) AS UDPResponseCnt
                           FROM
                           (
                               SELECT
                                   intDiv(ResponseLengthMap.Length > 4096 ? 4096 : ResponseLengthMap.Length, 16)*16 AS Len,
                                   sum(toUInt64(ResponseLengthMap.Count)) AS Cnt
                               FROM dsv_five_minute.QueryResponseLength
                               ARRAY JOIN ResponseLengthMap
                               WHERE Date='{date}'
                               AND TransportTCP=0
                               AND NodeID IN
                               (
                                  SELECT toUInt16(node_id)
                                  FROM dsv.node_text
                                  WHERE server_name='{server}'
                               )
                               GROUP BY Len
                           )
                           GROUP BY Name, Len
                           ORDER BY Len
                        """)),
                      (yaml_3colvalue,
                       textwrap.dedent("""\
                           SELECT
                               'tcp-request-sizes' AS Name,
                               Len = 288 ? '288-' : concat(toString(Len), '-', toString(Len + 15))AS TCPQueryLen,
                               sum(Cnt) AS TCPQueryCnt
                           FROM
                           (
                               SELECT
                                   intDiv(QueryLengthMap.Length > 288 ? 288 : QueryLengthMap.Length, 16)*16 AS Len,
                                   sum(toUInt64(QueryLengthMap.Count)) AS Cnt
                               FROM dsv_five_minute.QueryResponseLength
                               ARRAY JOIN QueryLengthMap
                               WHERE Date='{date}'
                               AND TransportTCP=1
                               AND NodeID IN
                               (
                                  SELECT toUInt16(node_id)
                                  FROM dsv.node_text
                                  WHERE server_name='{server}'
                               )
                               GROUP BY Len
                           )
                           GROUP BY Name, Len
                           ORDER BY Len
                        """)),
                      (yaml_3colvalue,
                       textwrap.dedent("""\
                           SELECT
                               'tcp-response-sizes' AS Name,
                               Len = 4096 ? '4096-' : concat(toString(Len), '-', toString(Len + 15))AS TCPResponseLen,
                               sum(Cnt) AS TCPResponseCnt
                           FROM
                           (
                               SELECT
                                   intDiv(ResponseLengthMap.Length > 4096 ? 4096 : ResponseLengthMap.Length, 16)*16 AS Len,
                                   sum(toUInt64(ResponseLengthMap.Count)) AS Cnt
                               FROM dsv_five_minute.QueryResponseLength
                               ARRAY JOIN ResponseLengthMap
                               WHERE Date='{date}'
                               AND TransportTCP=1
                               AND NodeID IN
                               (
                                  SELECT toUInt16(node_id)
                                  FROM dsv.node_text
                                  WHERE server_name='{server}'
                               )
                               GROUP BY Len
                           )
                           GROUP BY Name, Len
                           ORDER BY Len
                        """))],
    'traffic-volume': [(yaml_2colvalue,
                        textwrap.dedent("""\
                            SELECT
                                TransportTCP=0
                                    ?  (TransportIPv6
                                        ? 'dns-udp-queries-received-ipv6'
                                        : 'dns-udp-queries-received-ipv4')
                                    : (TransportIPv6
                                        ? 'dns-tcp-queries-received-ipv6'
                                        : 'dns-tcp-queries-received-ipv4') AS Name,
                                Queries,
                                TransportTCP=0
                                    ? (TransportIPv6 ? 1 : 0)
                                    : (TransportIPv6 ? 2 : 3) AS Order
                            FROM
                            (
                                SELECT
                                    TransportTCP,
                                    TransportIPv6,
                                    sum(toUInt64(QueryCount)) AS Queries
                                FROM dsv_five_minute.QueryResponseTransport
                                WHERE Date='{date}'
                                AND NodeID IN
                                (
                                    SELECT toUInt16(node_id)
                                    FROM dsv.node_text
                                    WHERE server_name='{server}' )
                                GROUP BY TransportTCP, TransportIPv6
                            )
                            GROUP BY Name, Order, Queries
                            ORDER BY Order
                       """)),
                       (yaml_2colvalue,
                        textwrap.dedent("""\
                            SELECT
                                TransportTCP=0
                                    ?  (TransportIPv6
                                        ? 'dns-udp-responses-sent-ipv6'
                                        : 'dns-udp-responses-sent-ipv4')
                                    : (TransportIPv6
                                        ? 'dns-tcp-responses-sent-ipv6'
                                        : 'dns-tcp-responses-sent-ipv4') AS Name,
                                Responses,
                                TransportTCP=0
                                    ? (TransportIPv6 ? 1 : 0)
                                    : (TransportIPv6 ? 2 : 3) AS Order
                            FROM
                            (
                                SELECT
                                    TransportTCP,
                                    TransportIPv6,
                                    sum(toUInt64(ResponseCount)) AS Responses
                                FROM dsv_five_minute.QueryResponseTransport
                                WHERE Date='{date}'
                                AND NodeID IN
                                (
                                    SELECT toUInt16(node_id)
                                    FROM dsv.node_text
                                    WHERE server_name='{server}' )
                                GROUP BY TransportTCP, TransportIPv6
                            )
                            GROUP BY Name, Order, Responses
                            ORDER BY Order
                       """))],
    'unique-sources': [(yaml_2colvalue,
                        textwrap.dedent("""\
                            SELECT
                                'num-sources-ipv4' AS Name,
                                uniqMerge(IPv4Addr) AS IPv4Cnt
                            FROM dsv_five_minute.UniqueIPv4Addr
                            WHERE Date='{date}'
                            AND NodeID IN
                            (
                                SELECT toUInt16(node_id)
                                FROM dsv.node_text
                                WHERE server_name='{server}' )
                       """)),
                       (yaml_2colvalue,
                        textwrap.dedent("""\
                            SELECT
                                'num-sources-ipv6' AS Name,
                                uniqMerge(IPv6Addr) AS IPv6Cnt
                            FROM dsv_five_minute.UniqueIPv6Addr
                            WHERE Date='{date}'
                            AND NodeID IN
                            (
                                SELECT toUInt16(node_id)
                                FROM dsv.node_text
                                WHERE server_name='{server}' )
                       """)),
                       (yaml_2colvalue,
                        textwrap.dedent("""\
                            SELECT
                                'num-sources-ipv6-aggregate' AS Name,
                                uniqMerge(IPv664Addr) AS IPv664Cnt
                            FROM dsv_five_minute.UniqueIPv6Addr
                            WHERE Date='{date}'
                            AND NodeID IN
                            (
                                SELECT toUInt16(node_id)
                                FROM dsv.node_text
                                WHERE server_name='{server}' )
                       """))],
    'zone-size': None,
}

def make_yaml(report, date, server, outdir, basename, ch_client, server_name, load_time_threshold):
    output = outdir / 'name'
    output = output.with_name(basename).with_suffix('.yaml')
    logging.debug('Generating RSSAC report YAML {} into {}'.format(report, output))

    yaml_data_list = YAML_DATA[report]
    if not yaml_data_list:
        logging.error('Report {report}: no data available'.format(report=report))
        return False

    body = ''
    ok_data = True
    for yaml_data in yaml_data_list:
        query = yaml_data[1].format(date=date, server=server,
                                    load_time_threshold=load_time_threshold)
        data = ch_client.execute(query)
        text, ok = yaml_data[0](data)
        if not ok:
            logging.error('Report {report}: missing data'.format(report=report))
        body += text
        ok_data = ok_data and ok

    with output.open('w') as outf:
        outf.write(yaml_header(report, server_name, date))
        outf.write(body)

    return ok_data

PANELS = {
    'rcode-volume': [(1, '')],
    'traffic-sizes': [(2, '-udp-query-small'), (3, '-tcp-query-small'),
                      (4, '-udp-response-small'), (5, '-tcp-response-small'),
                      (6, '-udp-query-big'), (7, '-tcp-query-big'),
                      (8, '-udp-response-big'), (9, '-tcp-response-big')],
    'traffic-volume': [(10, '-tcpipv4'), (11, '-tcpipv6'),
                       (12, '-udpipv4'), (13, '-udpipv6')],
    'unique-sources': [(18, '')],
    'load-time': [(19, '')],
    'zone-size': None
    }

def make_report_panel(output, url, no_cert_check):
    logging.debug('Generating RSSAC report panel {} into {}'.format(url, output))
    ctx = ssl.create_default_context()
    if no_cert_check:
        ctx.check_hostname = False
    with output.open('wb') as outf, urllib.request.urlopen(url, context=ctx) as page:
        shutil.copyfileobj(page, outf)

def make_report_panels(panel_list, date, server, outdir, basename, cfg, no_cert_check):
    if panel_list:
        for panel in panel_list:
            output = outdir / 'name'
            output = output.with_name(basename + panel[1]).with_suffix('.png')
            start = datetime.datetime.fromordinal(date.toordinal())
            end = start + datetime.timedelta(days=1)
            url = cfg['grafana-url'] + URL_FORMAT.format(
                start=int(start.timestamp())*1000,
                end=int(end.timestamp())*1000,
                server=server,
                panelid=panel[0])
            make_report_panel(output, url, no_cert_check)

def make_report(report, args, ch_client, cfg):
    outdir = \
        pathlib.Path(args.outdir) / args.date.strftime('%Y') / \
        args.date.strftime('%m') / report
    outdir.mkdir(parents=True, exist_ok=True)
    logging.info('Generating RSSAC report {} for {} into {}'.format(report, args.date, outdir))

    if not args.report_server_name:
        args.report_server_name = args.server.casefold()
    if not args.report_file_prefix:
        args.report_file_prefix = args.server.casefold()

    outbasename = '{}-{}-{}'.format(args.report_file_prefix, args.date.strftime('%Y%m%d'), report)

    if not args.no_plots:
        make_report_panels(PANELS[report], args.date, args.server,
                           outdir, outbasename, cfg, args.no_cert_check)

    ok_data = True
    if not args.no_yaml:
        ok_data = make_yaml(report, args.date, args.server, outdir, outbasename,
                            ch_client, args.report_server_name, int(cfg['load-time-threshold']))
    return ok_data

def add_args(parser):
    parser.add_argument('--date',
                        dest='date', action='store',
                        type=valid_date_type,
                        default=datetime.date.today() - datetime.timedelta(weeks=1),
                        help='generate reports for this date, default 7 days ago',
                        metavar='DATE')
    parser.add_argument('--output-dir',
                        dest='outdir', action='store',
                        default=None,
                        help='output directory for reports',
                        metavar='DIR')
    parser.add_argument('-r', '--report',
                        dest='report', action='store',
                        choices=REPORTS + ['all'],
                        required=True,
                        help='load-time, rcode-volume, traffic-sizes, ' \
                             'traffic-volume, unique-sources or all',
                        metavar='REPORT')
    parser.add_argument('-s', '--server',
                        dest='server', action='store',
                        required=True,
                        help='server name',
                        metavar='SERVER')
    parser.add_argument('--report-server-name',
                        dest='report_server_name', action='store',
                        default=None,
                        help='server name to appear on report, if different to server name',
                        metavar='SERVER')
    parser.add_argument('--report-file-prefix',
                        dest='report_file_prefix', action='store',
                        default=None,
                        help='prefix for report files, if different to server name',
                        metavar='PREFIX')
    parser.add_argument('--no-plots',
                        dest='no_plots', action='store_true',
                        help='do not generate plots')
    parser.add_argument('--no-yaml',
                        dest='no_yaml', action='store_true',
                        help='do not generate YAML')
    parser.add_argument('--no-cert-check',
                        dest='no_cert_check', action='store_true',
                        help='do not check Grafana certificate')

def main(args, cfg):
    clickhouse = cfg['clickhouse']
    ch_server = random.choice(clickhouse['servers'].split(',')).strip()
    ch_user = clickhouse['user']
    ch_pass = clickhouse['password']
    logging.debug('Using ClickHouse server {}'.format(ch_server))
    ch_client = clickhouse_driver.Client(host=ch_server, user=ch_user, password=ch_pass)

    rssac_cfg = cfg['rssac']
    if not args.outdir:
        args.outdir = rssac_cfg['outdir']

    ok_data = True
    try:
        if args.report == 'all':
            for arg in REPORTS:
                ok_data = ok_data and make_report(arg, args, ch_client, rssac_cfg)
        else:
            ok_data = make_report(args.report, args, ch_client, rssac_cfg)

        return 0 if ok_data else 1
    except (OSError, clickhouse_driver.errors.Error) as err:
        logging.error(err)
        print(err, file=sys.stderr)
        return 1
