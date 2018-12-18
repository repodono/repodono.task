# -*- coding: utf-8 -*-

try:
    import requests
    _session = requests.Session()
except ImportError:  # pragma: no cover
    _session = NotImplemented

# TODO should import from common base, but names are hard right now
from repodono.task import _root


class RequestsRoot(_root.BaseResourceRoot):
    """
    A root that make use of a requests.Session object.
    """

    def __init__(self, root=_session):
        if root is NotImplemented:
            raise ImportError('requests module is not available')
        self.root = root

    def _get(self, target):
        return self.root.get(target)

    def read(self, target):
        return self._get(target).content

    def text(self, target):
        return self._get(target).text
