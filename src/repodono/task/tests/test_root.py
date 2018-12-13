import unittest

from os import mkdir
from os.path import join
from os.path import pardir
from os.path import sep
from pathlib import Path
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
        self.assertEqual(b'safe', root.read(target))
        self.assertEqual('safe', root.text(target))

    def test_root_absolute_access(self):
        root = FSRoot(self.safe)
        # using forward slashes to verify support for unnormalized input
        # target which could be from some HTTP request.
        self.assertEqual(b'safe', root.read('/readme.txt'))
        self.assertEqual('safe', root.text('/readme.txt'))

    def test_root_traversal_blocked(self):
        root = FSRoot(self.safe)
        self.assertEqual('safe_unsafe', root.text('../unsafe/readme.txt'))
        # verify that failure will happen with a native join
        target = sep.join([pardir, 'unsafe', 'readme.txt'])
        with open(join(str(root.root), target)) as fd:
            self.assertEqual('unsafe', fd.read())

    def test_non_files_blocked(self):
        root = FSRoot(self.safe)
        with self.assertRaises(FileNotFoundError):
            root.text('/unsafe')

        with self.assertRaises(FileNotFoundError):
            root.read('/unsafe')

    def test_symlink_indirection_stopped(self):
        raw_dir = join(self.unsafe, 'outside')
        mkdir(raw_dir)

        symlink = Path(join(self.unsafe, 'link'))
        # to simplify inferrence filtering, create an actual valid link
        # inside the unsafe directory that links to a valid location
        symlink.symlink_to(self.safe, target_is_directory=True)
        # ensure that the link is created correctly such that this test
        # case will execute as expected
        self.assertTrue(symlink.resolve().samefile(self.safe))

        root = FSRoot(self.safe)
        with self.assertRaises(FileNotFoundError):
            root.text('../unsafe/link/readme.txt')

        # a more comprehensive example is that if this is not filtered,
        # attacker can infer the existence of some symlink inside /etc
        # that links to /opt and create a relative path that traverse
        # into a valid location that is inside the root.

    def test_symlink_filtered(self):
        raw_dir = join(self.unsafe, 'outside')
        mkdir(raw_dir)
        with open(join(raw_dir, 'secure.txt'), 'w') as fd:
            fd.write('secrets')

        symlink = Path(join(self.safe, 'link'))
        symlink.symlink_to(
            sep.join(['..', 'unsafe', 'outside']), target_is_directory=True)
        # ensure that the link is created correctly such that this test
        # case will execute as expected
        self.assertTrue(symlink.resolve().samefile(raw_dir))

        root = FSRoot(self.safe)
        with self.assertRaises(FileNotFoundError):
            root.text('/link/secure.txt')
