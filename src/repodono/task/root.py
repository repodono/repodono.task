# -*- coding: utf-8 -*-

from os.path import normpath
from pathlib import Path


class BaseResourceRoot(object):
    """
    Represents a supported base resource root.
    """

    def __init__(self, root):
        self.root = root

    def read(self, target):
        """
        Fetch the target and return a string.
        """

        raise NotImplementedError()


class FSRoot(BaseResourceRoot):
    """
    Lock a directory as the root dir for some operations.
    """

    def __init__(self, root):
        # TODO figure out what to do if self.root != root, e.g. warning?
        self.root = Path(root).resolve()
        # also track the OS specific root identifier
        self._os_root = Path(self.root.root)

    def read(self, target):
        # normalize the input target by joining it with the real
        # filesystem root and use the OS specific path normalization
        # function; not using Path.resolve because it also invokes
        # realpath which resolves symlinks on the filesystem of the
        # system that is executing this code on behalf of some other
        # party.  The other party may also control paths which if
        # the resolved paths are normalized into some symlink that
        # exists, Path.resolve will then normalize that which may then
        # result into that path, which will reveal to an attacker that
        # such symlinks exists.
        parts = Path(
            normpath(self._os_root.joinpath(*Path(target).parts))).parts[1:]
        # naturally, remove the leading root fragment before joining
        # with the root defined for this instance.
        target = self.root.joinpath(*parts)
        with open(target) as fd:
            return fd.read()
