# -*- coding: utf-8 -*-

from collections import Iterable
from os.path import normpath
from pathlib import Path

# TODO should import from common base, but names are hard right now
from repodono.task._root import (
    NotImplementedResourceRoot,
    BaseResourceRoot,
)
from repodono.task import _requests_root

RequestsRoot = (
    NotImplementedResourceRoot
    if _requests_root._session is NotImplemented else
    _requests_root.RequestsRoot
)


class FSRoot(BaseResourceRoot):
    """
    Lock a directory as the root dir for some operations.
    """

    def __init__(self, root):
        # TODO figure out what to do if self.root != root, e.g. warning?
        self.root = Path(root).resolve()
        # also track the OS specific root identifier
        self._os_root = Path(self.root.root)

    def _resolve(self, target):
        if isinstance(target, str):
            subparts = Path(target).parts
        elif isinstance(target, Iterable):
            subparts = tuple(target)
        else:
            raise TypeError(
                "'root' must be either str or an iterable of strs")

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
            normpath(self._os_root.joinpath(*subparts))).parts[1:]
        full_target = self.root.joinpath(*parts).resolve()

        try:
            # Now, ensure that the internal symlinks are not absolute or
            # reference outside of the declared root.
            full_target.relative_to(self.root)
        except ValueError:
            raise FileNotFoundError(target)

        return full_target

    def _resolve_file(self, target):
        full_target = self._resolve(target)

        if not full_target.is_file():
            # Directories can't be read, so simply raise this.
            raise FileNotFoundError(target)

        return full_target

    def read(self, target):
        with open(self._resolve_file(target), 'rb') as fd:
            return fd.read()

    def text(self, target):
        with open(self._resolve_file(target), 'r') as fd:
            return fd.read()
