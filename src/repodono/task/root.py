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

    def _join_path_parts(self, parts):
        yield self.root.joinpath(*parts).resolve()

    def _resolve(self, target):
        """
        Generator for valid full_targets
        """

        if isinstance(target, str):
            subparts = Path(target).parts
        elif isinstance(target, Iterable):
            subparts = tuple(target)
        else:
            raise TypeError(
                "'target' must be either str or an iterable of strs")

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

        for full_target in self._join_path_parts(parts):
            try:
                # Now, ensure that the internal symlinks are not absolute or
                # reference outside of the declared root.
                full_target.relative_to(self.root)
            except ValueError:
                continue

            yield full_target

    def resolve(self, target):
        """
        Resolve target from this root on the filesystem.  If the
        provided target is valid, return the Path object.
        """

        for full_target in self._resolve(target):
            return full_target
        raise FileNotFoundError(target)

    def _resolve_file(self, target):
        for resolved_target in self._resolve(target):
            if resolved_target.is_file():
                return resolved_target
        else:
            # ran out of targets
            raise FileNotFoundError(target)

    def _read_target_fd(self, target, fd):
        return fd.read()

    def read(self, target):
        resolved_target = self._resolve_file(target)
        with open(resolved_target, 'rb') as fd:
            return self._read_target_fd(resolved_target, fd)

    def text(self, target):
        resolved_target = self._resolve_file(target)
        with open(resolved_target, 'r') as fd:
            return self._read_target_fd(resolved_target, fd)


class FilterFextRoot(FSRoot):

    def __init__(self, root, fext_filters):
        """
        Arguments:

        root
            The root for this instance
        fext_filters
            The list of file extension filters
        """

        self._fext_filters_map = dict(fext_filters)
        self._fext_filters = tuple(self._fext_filters_map.items())
        super().__init__(root)

    @staticmethod
    def default(content):
        return content

    def _join_path_parts(self, parts):
        for fext, filters in self._fext_filters:
            if fext[:1] != '.':
                # silently ignoring badly defined filename extensions
                continue
            yield self.root.joinpath(
                *(parts[:-1] + (parts[-1] + fext,))
            ).resolve()

    def _read_target_fd(self, target, fd):
        return self._fext_filters_map[target.suffix](fd.read())
