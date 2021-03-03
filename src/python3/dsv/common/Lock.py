# Copyright 2018-2019 Internet Corporation for Assigned Names and Numbers.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, you can obtain one at https://mozilla.org/MPL/2.0/.
#
# Developed by Sinodun IT (sinodun.com)

import fcntl
import pathlib
import pwd
import os

class NoSuchUserException(Exception):
    """Exception raised when there is no such user as the one specified for locking."""
    def __init__(self, user):
        super().__init__("Configured user {} does not exist.".format(user))

class WrongUserException(Exception):
    """Exception raised when we aren't the right user to use a Visualizer lock."""
    def __init__(self, user):
        super().__init__("You need to be user {} to use this command.".format(user))

class DSVUser:
    # pylint: disable=too-few-public-methods
    def __init__(self, user):
        self._user = user
        try:
            passwd = pwd.getpwnam(user)
            self._uid = passwd.pw_uid
            self._gid = passwd.pw_gid
        except KeyError:
            raise NoSuchUserException(user)

    def ensure_user(self):
        """Ensure we are the nominated user."""
        try:
            os.setgid(self._gid)
            os.setuid(self._uid)
        except PermissionError:
            raise WrongUserException(self._user)

class DSVLock:
    def __init__(self, user, lockpath):
        self._lock = pathlib.Path(lockpath)
        self._user = DSVUser(user)

    def _ensure_lockfile(self):
        # pylint: disable=no-member
        """Ensure the lockfile and its dir exist."""
        self._user.ensure_user()
        lockdir = self._lock.parent
        lockdir.mkdir(0o755, parents=True, exist_ok=True)
        self._lock.touch(0o666)

    def _get_mode(self):
        """Get the current lockfile mode."""
        return self._lock.stat().st_mode

    def lock(self):
        """Obtain the lock, or throw.

        WrongUserException: Incorrect user permissions.
        PermissionError: Lock frozen.
        BlockingError: Lock already taken.
        """
        self._ensure_lockfile()
        f = self._lock.open('w')
        fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def is_frozen(self):
        """Is the lock currently frozen?

        So status can be read by all users, assume not frozen
        if the lock file does not exist but directory is readable."""
        try:
            if not self._lock.exists():
                return False
        except PermissionError:
            self._ensure_lockfile()
        return (self._get_mode() & 0o200) == 0

    def freeze(self):
        """Freeze the lock.

        Set permissions to read-only.
        """
        self._ensure_lockfile()
        self._lock.chmod(self._get_mode() & 0o444)

    def thaw(self):
        """Thaw the lock.

        Set permissions to read/write.
        """
        self._ensure_lockfile()
        self._lock.chmod(self._get_mode() | 0o200)
