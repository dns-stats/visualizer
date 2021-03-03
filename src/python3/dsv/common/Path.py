# Copyright 2018-2019 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import datetime
import os.path
import pathlib

INCOMING_DIR = 'incoming'
CDNS_DIR = 'cbor'
PCAP_DIR = 'pcap'
PENDING_DIR = 'pending'
ERROR_DIR = 'error'           # Dir is ERROR_DIR+'-<queue-name>'.

_KNOWN_DIRS = [INCOMING_DIR, CDNS_DIR, PCAP_DIR, ERROR_DIR]

class UnknownDirError(Exception):
    """Exception raised when an unknown directory is found in a Visualizer path."""
    def __init__(self, dpath):
        super().__init__("Unknown Visualizer directory {}".format(dpath))

class NoFileError(Exception):
    """Exception raised when asked for a file but none given."""
    def __init__(self):
        super().__init__("No file.")

def error_dir_base_name(queue_name):
    return '{base}-{queue}'.format(base=ERROR_DIR, queue=queue_name)

class DSVPath:
    def __init__(self, path):
        self._path = p = pathlib.Path(path)
        if p.is_dir():
            self._filename = None
        else:
            self._filename = p.name
            p = p.parent
        if p.name == PENDING_DIR:
            p = p.parent
        if p.name not in [INCOMING_DIR, CDNS_DIR, PCAP_DIR] and not p.name.startswith(ERROR_DIR):
            raise UnknownDirError(p.name)
        p = p.parent
        self._node = p.name
        p = p.parent
        self._server = p.name
        self._base = p.parent

    @property
    def server(self):
        return self._server

    @property
    def node(self):
        return self._node

    @property
    def path(self):
        return self._path

    @property
    def server_dir_path(self):
        return self._base / self._server

    @property
    def incoming_dir_path(self):
        return self._base / self._server / self._node / INCOMING_DIR

    @property
    def incoming_pending_dir_path(self):
        return self._base / self._server / self._node / INCOMING_DIR / PENDING_DIR

    @property
    def cdns_dir_path(self):
        return self._base / self._server / self._node / CDNS_DIR

    @property
    def cdns_pending_dir_path(self):
        return self._base / self._server / self._node / CDNS_DIR / PENDING_DIR

    @property
    def pcap_dir_path(self):
        return self._base / self._server / self._node / PCAP_DIR

    @property
    def pcap_pending_dir_path(self):
        return self._base / self._server / self._node / PCAP_DIR / PENDING_DIR

    def error_dir_path(self, queue_name):
        return self._base / self._server / self._node / error_dir_base_name(queue_name)

    @property
    def incoming_file_path(self):
        if not self._filename:
            raise NoFileError()
        return self.incoming_dir_path / self._filename

    @property
    def incoming_pending_file_path(self):
        if not self._filename:
            raise NoFileError()
        return self.incoming_pending_dir_path / self._filename

    @property
    def cdns_file_path(self):
        if not self._filename:
            raise NoFileError()
        return self.cdns_dir_path / self._filename

    @property
    def cdns_pending_file_path(self):
        if not self._filename:
            raise NoFileError()
        return self.cdns_pending_dir_path / self._filename

    @property
    def pcap_file_path(self):
        if not self._filename:
            raise NoFileError()
        return self.pcap_dir_path / self._filename

    @property
    def pcap_pending_file_path(self):
        if not self._filename:
            raise NoFileError()
        return self.pcap_pending_dir_path / self._filename

    def error_file_path(self, queue_name):
        if not self._filename:
            raise NoFileError()
        return self.error_dir_path(queue_name) / self._filename

    def datetime(self):
        """Return a date/time associated with the file.

           If the filename is not a Visualizer timestamp, return the
           file last modified time.
        """
        if not self._filename:
            raise NoFileError()
        try:
            return datetime.datetime.strptime(self._filename[0:15], '%Y%m%d-%H%M%S')
        except ValueError:
            return datetime.datetime.utcfromtimestamp(os.path.getmtime(self._path))
