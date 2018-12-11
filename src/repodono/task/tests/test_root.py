import unittest

from os import mkdir
from os.path import join
from os.path import sep
from os.path import pardir
from tempfile import TemporaryDirectory

from repodono.task.root import FSRoot


class FSRootTestCase(unittest.TestCase):

    def setUp(self):
        self.base = TemporaryDirectory()
        self.unsafe = join(self.base.name, 'unsafe')
        self.safe = join(self.base.name, 'safe')
        self.safe_unsafe = join(self.base.name, 'safe', 'unsafe')
        mkdir(self.unsafe)
        mkdir(self.safe)
        mkdir(self.safe_unsafe)

        with open(join(self.safe, 'readme.txt'), 'w') as fd:
            fd.write('safe')

        with open(join(self.safe_unsafe, 'readme.txt'), 'w') as fd:
            fd.write('safe_unsafe')

        with open(join(self.unsafe, 'readme.txt'), 'w') as fd:
            fd.write('unsafe')

    def tearDown(self):
        self.base.cleanup()

    def test_root_relative_access(self):
        root = FSRoot(self.safe)
        target = 'readme.txt'
        self.assertEqual('safe', root.read(target))

    def test_root_absolute_access(self):
        root = FSRoot(self.safe)
        target = sep.join(['', 'readme.txt'])
        self.assertEqual('safe', root.read(target))

    def test_root_traversal_blocked(self):
        root = FSRoot(self.safe)
        target = sep.join([pardir, 'unsafe', 'readme.txt'])
        self.assertEqual('safe_unsafe', root.read(target))
        # verify that failure will happen with a native join
        with open(join(str(root.root), target)) as fd:
            self.assertEqual('unsafe', fd.read())

    # TODO symlinks??
