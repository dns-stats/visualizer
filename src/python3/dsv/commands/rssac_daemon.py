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
# Listen for NOTIFY messages on a zone, and when we get one for the
# zone of interest, run notifier program and pass it the serial number.
#
# This program typically listens on port 53. We use the good offices
# of systemd to handle all the socket setup, and configure it to pass
# us a single socket to work with. We therefore avoid all the brouhaha
# associated with running as root, dropping privs etc.
#

import logging
import socket
import socketserver
import subprocess

import dns.exception
import dns.message
import dns.opcode

import systemd.daemon

description = 'listen for notifications to trigger RSSAC zone stats collection.'

class RSSACHandler(socketserver.DatagramRequestHandler):
    def handle(self):
        data = self.request[0]
        try:
            message = dns.message.from_wire(data)
            if self.send_response(message):
                response = dns.message.make_response(message)
                self.socket.sendto(response.to_wire(), self.client_address)
                self.run_notify(message)
        except (dns.exception.DNSException, OSError) as err:
            logging.error('Error {err} on data from {client}'.format(
                err=err, client=self.client_address[0]))

    def send_response(self, message):
        # pylint: disable=no-member
        if message.opcode() != dns.opcode.NOTIFY:
            logging.info('Non-NOTIFY from {client}, ignoring'.format(
                client=self.client_address[0]))
            return False

        if len(message.question) == 0:
            logging.info('NOTIFY from {client} with no question, ignoring'.format(
                client=self.client_address[0]))
            return False

        qname = str(message.question[0].name)
        if self.server.zone != qname:
            logging.info('NOTIFY from {client} for zone "{zone}" not "{server}", ignoring'.format(
                client=self.client_address[0],
                zone=qname,
                server=self.server.zone))
            return False

        return True

    def run_notify(self, message):
        if len(message.answer) == 0:
            logging.error('NOTIFY from {client} has no serial, ignoring'.format(
                client=self.client_address[0]))
            return

        serial = message.answer[0].to_rdataset()[0].serial

        logging.info('NOTIFY from {client} serial {serial}'.format(
            client=self.client_address[0],
            serial=serial))
        try:
            subprocess.run([self.server.notifier, str(serial)], check=True)
        except (subprocess.SubprocessError, OSError) as err:
            logging.error('dsv-rssac-notify: {}'.format(err))

class RSSACServer(socketserver.UDPServer):
    def __init__(self, fd, family, handler, notifier, zone):
        super().__init__(None, handler, bind_and_activate=False)
        self.socket = socket.fromfd(fd, family, self.socket_type)
        self.notifier = notifier
        self.zone = zone

def add_args(parser):
    parser.add_argument('--notifier',
                        dest='notifier', action='store',
                        default='dsv-rssac-notify',
                        help='notification process to run (default %(default)s)',
                        metavar='NOTIFIER')
    parser.add_argument('-t', '--socket-type',
                        dest='socktype', action='store',
                        choices=['ipv4', 'ipv6'],
                        required=True,
                        help='Type of socket systemd is listening on')

def main(args, cfg):
    fds = systemd.daemon.listen_fds()
    if len(fds) != 1:
        logging.error('Requires a single socket from systemd')
        return 1
    fd = fds[0]
    if not systemd.daemon.is_socket(fd):
        logging.error('Passed object from systemd is not a socket')
        return 1

    family = socket.AF_INET if args.socktype == 'ipv4' else socket.AF_INET6
    server = RSSACServer(fd, family, RSSACHandler, args.notifier, cfg['rssac']['zone'])
    logging.debug('RSSAC daemon started')
    server.serve_forever()
    # Keep pylint happy.
    return 0
