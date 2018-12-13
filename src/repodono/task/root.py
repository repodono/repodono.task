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
        # such symlinks exists with this initial target.

        # So instead of
        # full_target = self.root.joinpath(target).resolve()
        # Do this (naturally, have the leading root fragment removed):
        parts = Path(
            normpath(self._os_root.joinpath(*Path(target).parts))).parts[1:]
        full_target = self.root.joinpath(*parts).resolve()

        try:
            # Now, ensure that the internal symlinks are not absolute or
            # reference outside of the declared root.
            full_target.relative_to(self.root)
        except ValueError:
            raise FileNotFoundError(target)

        if not full_target.is_file():
            # Also, ensure that the items are fiels.
            raise FileNotFoundError(target)

        with open(full_target) as fd:
            return fd.read()
