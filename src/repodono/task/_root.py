# -*- coding: utf-8 -*-


class BaseResourceRoot(object):
    """
    Represents a supported base resource root.
    """

    def __init__(self, root):
        self.root = root

    def read(self, target):
        """
        Fetch the target and return the raw bytes
        """

        raise NotImplementedError()

    def text(self, target):
        """
        Fetch the target and return a string.
        """

        raise NotImplementedError()


class NotImplementedResourceRoot(object):

    def __init__(self, root):
        raise NotImplementedError()
