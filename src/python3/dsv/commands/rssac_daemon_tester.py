#!/usr/bin/env python3
#
# Copyright 2019-2020 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)
#
# Send a NOTIFY to the designated server and port with the given zone
# and serial number.
#

import socket
import sys

import dns.exception
import dns.message
import dns.opcode
import dns.rdatatype
import dns.rrset
import dns.query

description = 'send a NOTIFY to test the RSSAC daemon.'

def add_args(parser):
    parser.add_argument('-s', '--server',
                        dest='server', action='store',
                        default='localhost',
                        help='server to send message to (default %(default)s)',
                        metavar='SERVER')
    parser.add_argument('-p', '--port',
                        dest='port', action='store', type=int,
                        default=53,
                        help='port to send message to (default %(default)s)',
                        metavar='PORT')
    parser.add_argument('-n', '--serial',
                        dest='serial', action='store', type=int,
                        required=True,
                        help='serial number',
                        metavar='SERIAL')
    parser.add_argument('-z', '--zone',
                        dest='zone', action='store',
                        required=True,
                        help='the zone',
                        metavar='ZONE')

def main(args, _):
    # pylint: disable=no-member
    message = dns.message.make_query(args.zone, dns.rdatatype.SOA)
    message.set_opcode(dns.opcode.NOTIFY)
    rrset = dns.rrset.from_text(args.zone, 0, 'IN', 'SOA', '. . {} 0 0 0 0'.format(args.serial))
    message.answer.append(rrset)

    try:
        # dns.query.udp needs a string with an IP address.
        # Otherwise it messes up address comparison on the return packet.
        dest = socket.getaddrinfo(args.server, args.port)
        server_addr = dest[0][4][0]
    except OSError:
        print('Unknown server {}'.format(args.server), file=sys.stderr)
        return 1

    try:
        dns.query.udp(message, server_addr, port=args.port, timeout=1)
        return 0
    except dns.exception.Timeout:
        print('No response received.', file=sys.stderr)
        return 1
