#!/usr/bin/env python3
#
# Copyright 2019, 2020, 2021 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Check ClickHouse zone tables to see if we have information on the
# zone serial passed as argument. If not, and the serial is later than
# the last one seen, obtain query all Visualizer nodes via their service
# address to get the latency, and do an XFR on the zone at a configured
# server to find its size.
#

import datetime
import logging
import random
import selectors
import socket
import sys
import textwrap

import dns.message
import dns.rdatatype

import psycopg2

import clickhouse_driver
import clickhouse_driver.errors

import dsv.common.NodeFlag as dnf

description = 'update Visualizer zone RSSAC data.'

class NotifyError(Exception):
    pass

def cmp_serial(a, b):
    # pylint: disable=invalid-name
    """Compare serial numbers. -1 if a is before b, 0 if a=b, else 1.

       Do comparison using RFC1982.
    """
    if a == b:
        return 0
    if (a < b and (b - a) < (2**31 - 1)) or (a > b and (a - b) > (2**31 - 1)):
        return -1
    return 1

def find_latest_serial(serials):
    """Find latest zone serial in a list of serials."""
    res = None
    for s in serials:
        if not res or cmp_serial(res, s) < 0:
            res = s
    return res

def latest_serial(ch_client, zone, server):
    """Find the latest zone serial for the server.

       Look back through the last month and select the latest serial
       seen for the named server.
    """
    recs = ch_client.execute(textwrap.dedent("""\
              SELECT
                  Serial
              FROM dsv.ZoneLatency
              WHERE Date >= subtractMonths(today(), 1) AND Date <= today()
              AND Zone='{zone}'
              AND NodeID IN
              (
                  SELECT toUInt16(node_id)
                  FROM dsv.node_text
                  WHERE server_name='{server}' )""".format(zone=zone, server=server)))

    return find_latest_serial([r[0] for r in recs])

def get6addr(name):
    """Get IPv6 address for name. If necessary, an IPv4 over IPv6 address."""
    try:
        addr = socket.getaddrinfo(name, 'domain', family=socket.AF_INET6)
    except socket.gaierror:
        addr = socket.getaddrinfo(name, 'domain')
        addr6 = '::ffff:' + addr[0][4][0]
        addr = socket.getaddrinfo(addr6, 'domain', family=socket.AF_INET6)
    return addr[0][4]

def make_query_list(nodelist, zone):
    """Make a list of queries for each node with no current latency value.

       Pick a random starting query ID, and increment from there.
       Return a list of node IDs for the nodes that correspond
       to the entries in the query list. The idea is that when we
       get a response with an ID in our range, we can update that node's
       information.
    """
    first_id = random.randint(1, 32000 - len(nodelist))
    qid = first_id
    nids = []
    querylist = []
    for nid, n in nodelist.items():
        if 'latency' not in n:
            # pylint: disable=no-member
            q = dns.message.make_query(zone, dns.rdatatype.SOA)
            q.id = qid
            nids.append(nid)
            querylist.append((q, n['addr']))
            qid += 1
    return (first_id, nids, querylist)

def send_and_receive(queries, nodelist, serial, sock, start_time, total_nodes):
    """Send queries and receive responses.

       When we get a response with a serial matching the expected,
       store the latency into the node information.
    """
    (first_id, nids, querylist) = queries
    to_receive = len(querylist)

    # Start by listening for read and write ready. Once we've finished
    # sending queries, switch to listening for read only.
    sel = selectors.DefaultSelector()
    sel.register(sock, selectors.EVENT_READ | selectors.EVENT_WRITE)

    while querylist or to_receive > 0:
        events = sel.select(1)
        # No action for a second? Give up on this pass.
        if not events:
            break

        if events[0][1] & selectors.EVENT_WRITE:
            if not querylist:
                sel.unregister(sock)
                sel.register(sock, selectors.EVENT_READ)
                continue
            q = querylist.pop()
            sock.sendto(q[0].to_wire(), q[1])

        if events[0][1] & selectors.EVENT_READ:
            (wire, from_addr) = sock.recvfrom(65535)
            try:
                reply = dns.message.from_wire(wire)
                i = reply.id - first_id
                if i < 0 or i >= len(nids):
                    logging.warning('DNS response from {addr}: ID out of range'.format(
                        addr=from_addr))
                    continue
                if not reply.answer:
                    logging.warning('DNS response from {addr}: No Answer RR'.format(
                        addr=from_addr))
                    continue
                rec_serial = reply.answer[0].to_rdataset()[0].serial
                serial_match = cmp_serial(serial, rec_serial)
                if serial_match == 0:
                    to_receive -= 1
                    now = datetime.datetime.now()
                    nodelist[nids[i]]['latency'] = int((now - start_time).total_seconds())
                    nodelist[nids[i]]['time'] = now
                    nodelist[nids[i]]['percent_done'] = \
                        int(((total_nodes - to_receive) * 100)/total_nodes)
                elif serial_match < 0:
                    sel.unregister(sock)
                    raise NotifyError('Serial {serial} obsolete, '
                                      'zone has {rec_serial}'.format(
                                          serial=serial,
                                          rec_serial=rec_serial))
            except dns.exception.FormError:
                logging.warning('Response from {addr}: Not a DNS packet'.format(
                    addr=from_addr))

    sel.unregister(sock)
    return to_receive

def update_latency_table(ch_client, zone, serial, nodelist, dryrun):
    values = []
    for nid, n in nodelist.items():
        if 'latency' in n:
            if dryrun:
                print('Node ID {nid} zone {zone} serial {serial}: latency '
                      '{latency} percent nodes updated {percent} at {date}'.format(
                          nid=nid, zone=zone, serial=serial,
                          latency=n['latency'], percent=n['percent_done'],
                          date=n['time']))
            else:
                logging.debug('Node ID {nid} zone {zone} serial {serial}: '
                              'latency {latency} percent {percent} at {date}'.format(
                                  nid=nid, zone=zone,
                                  serial=serial, latency=n['latency'],
                                  percent=n['percent_done'], date=n['time']))
                values.append({'Date': n['time'].date(),
                               'DateTime': n['time'],
                               'NodeID': nid,
                               'Zone': zone,
                               'Serial': serial,
                               'Latency': n['latency'],
                               'PercentNodesUpdated': n['percent_done']})
        else:
            logging.warning('No response from node {name}'.format(name=n['name']))

    if values:
        ch_client.execute(
            'INSERT INTO dsv.ZoneLatency(Date, DateTime, NodeID, Zone, '
            'Serial, Latency, PercentNodesUpdated) VALUES',
            values)

def getnodelist(pgcur, server):
    """Get the list of servers to be examined.

       We do not examine servers with no service address or servers
       flagged as either inactive or not for RSSAC.

       Return a dictionary with service address, node_id and node names.
       We read the data from Postgres so we can avoid exposing the
       service addresses to ClickHouse.
    """
    res = {}
    flagmask = dnf.NodeFlag.NOT_RSSAC.value
    pgcur.execute('SELECT service_addr, id, name FROM node '
                  'WHERE length(service_addr) > 0 AND '
                  '(flags & %s)=0 AND '
                  'server_id=(SELECT id FROM node_server WHERE name=%s)',
                  (flagmask, server,))
    for rec in pgcur:
        try:
            addr = get6addr(rec[0])
            res[rec[1]] = {'addr': addr, 'name': rec[2]}
        except OSError as ose:
            logging.warning('Bad service address "{addr}" for node {node}: {err}'.format(
                addr=rec[0], node=rec[2], err=ose))
    return res

def latencies(ch_client, nodelist, zone, serial, timeout, dryrun, percent_required):
    """Obtain latencies for server nodes.

       Send SOA queries and collect responses to all nodes in the
       list (actually dictionary) until we're all done or we time out.
    """
    with socket.socket(family=socket.AF_INET6, type=socket.SOCK_DGRAM) as inet6_sock:
        inet6_sock.setblocking(False)
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(seconds=timeout)
        total_nodes = len(nodelist)
        outstanding = total_nodes

        while datetime.datetime.now() < end_time:
            queries = make_query_list(nodelist, zone)
            outstanding = send_and_receive(queries, nodelist, serial,
                                           inet6_sock, start_time, total_nodes)
            if outstanding == 0:
                break

    update_latency_table(ch_client, zone, serial, nodelist, dryrun)

    percent_updated = ((total_nodes - outstanding) * 100) // total_nodes
    if percent_updated < percent_required:
        logging.error('{updated}% nodes updated, under required threshold '
                      '{required}%'.format(updated=percent_updated, required=percent_required))
        return False
    return True

def add_args(parser):
    parser.add_argument('-n', '--dry-run',
                        dest='dryrun', action='store_true', default=False,
                        help='perform a trial run')
    parser.add_argument('-t', '--timeout', type=int,
                        dest='timeout', action='store', default=800,
                        help='timeout finding latencies (default %(default)s)',
                        metavar='SECONDS')
    parser.add_argument('serial', type=int,
                        help='zone serial number',
                        metavar='SERIAL')

def main(args, cfg):
    logging.debug('dsv-rssac-notify called, serial {}'.format(args.serial))
    clickhouse = cfg['clickhouse']
    ch_server = random.choice(clickhouse['servers'].split(',')).strip()
    ch_user = clickhouse['user']
    ch_pass = clickhouse['password']
    logging.debug('Using ClickHouse server {}'.format(ch_server))

    pgcfg = cfg['postgres']

    rssaccfg = cfg['rssac']
    server = rssaccfg['server']
    zone = rssaccfg['zone']
    percent = int(rssaccfg['load-time-threshold'])

    try:
        ch_client = clickhouse_driver.Client(host=ch_server, user=ch_user, password=ch_pass)
        pgconn = psycopg2.connect(host=pgcfg['host'],
                                  dbname=pgcfg['database'],
                                  user=pgcfg['user'],
                                  password=pgcfg['password'])
        with pgconn.cursor() as pgcur:
            nodelist = getnodelist(pgcur, server)
        pgconn.close()

        latest = latest_serial(ch_client, zone, server)
        if latest and cmp_serial(latest, args.serial) >= 0:
            logging.debug('Serial {serial} is not newer than the latest known ({latest}).'.format(
                serial=args.serial, latest=latest))
            return 0

        ok = latencies(ch_client, nodelist, zone, args.serial, args.timeout, args.dryrun, percent)
        return 0 if ok else 1
    except NotifyError as err:
        logging.warning(err)
        return 0
    except (OSError, clickhouse_driver.errors.Error) as err:
        logging.error(err)
        print(err, file=sys.stderr)
        return 1
