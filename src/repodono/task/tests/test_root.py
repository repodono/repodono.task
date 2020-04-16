import unittest

from collections import namedtuple
from os import mkdir
from os.path import join
from os.path import pardir
from os.path import sep
from pathlib import Path
from tempfile import TemporaryDirectory

from repodono.task.root import (
    FSRoot,
    FilterFextRoot,
    BaseResourceRoot,
    NotImplementedResourceRoot,
    RequestsRoot,
)


class NotImplementedTestCase(unittest.TestCase):

    def test_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            NotImplementedResourceRoot(None)

        root = BaseResourceRoot(None)

        with self.assertRaises(NotImplementedError):
            root.text('foo')

        with self.assertRaises(NotImplementedError):
            root.read('foo')


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

    def test_root_resolve_normal(self):
        root = FSRoot(self.safe)
        self.assertEqual(
            Path(join(self.safe, 'target')),
            root.resolve('target'),
        )

        self.assertEqual(
            Path(join(self.safe, 'target')),
            root.resolve('/target'),
        )

        self.assertEqual(
            Path(join(self.safe, 'target')),
            root.resolve('../target'),
        )

    def test_root_resolve_symlink_blocked(self):
        raw_dir = join(self.unsafe, 'outside')
        mkdir(raw_dir)

        symlink = Path(join(self.safe, 'link'))
        # to simplify inferrence filtering, create an actual valid link
        # inside the unsafe directory that links to a valid location
        symlink.symlink_to(self.unsafe)
        # ensure that the link is created correctly such that this test
        # case will execute as expected
        self.assertTrue(symlink.resolve().samefile(self.unsafe))

        root = FSRoot(self.safe)
        with self.assertRaises(FileNotFoundError):
            root.resolve('link')

    def test_root_relative_access(self):
        root = FSRoot(self.safe)
        target = 'readme.txt'
        self.assertEqual(b'safe', root.read(target))
        self.assertEqual('safe', root.text(target))

    def test_root_subdir_access(self):
        root = FSRoot(self.base.name)
        target = ['safe', 'readme.txt']

        # joined path
        self.assertEqual(b'safe', root.read(sep.join(target)))
        self.assertEqual('safe', root.text(sep.join(target)))

        # raw list access
        self.assertEqual(b'safe', root.read(target))
        self.assertEqual('safe', root.text(target))

        with self.assertRaises(TypeError):
            root.read(object)

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

        # repeating the resolve test
        symlink = Path(join(self.safe, 'link'))
        symlink.symlink_to(self.unsafe)
        self.assertTrue(symlink.resolve().samefile(self.unsafe))

        root = FSRoot(self.safe)
        with self.assertRaises(FileNotFoundError):
            root.text('link/readme.txt')

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


@unittest.skipIf(
    RequestsRoot is NotImplementedResourceRoot,
    'the requests package is not installed')
class RequestsRootTestCase(unittest.TestCase):
    """
    The tests in this class are structured such that the proper API
    calls through the requests library are used .
    """

    FakeResponse = namedtuple('FakeResponse', ['content', 'text'])

    def setUp(self):
        # default response.
        self.response = self.FakeResponse(b'content', 'text')

    def fake_session(self):
        class FakeSession(object):
            def get(self_, target):
                return self.response

        return FakeSession()

    def test_fail(self):
        with self.assertRaises(ImportError):
            RequestsRoot(NotImplemented)

    def test_base(self):
        root = RequestsRoot()
        # just check for existence.
        self.assertTrue(root.root)

    def test_access(self):
        root = RequestsRoot(self.fake_session())
        self.assertEqual('text', root.text('somewhere'))
        self.assertEqual(b'content', root.read('somewhere'))

        # change the response
        self.response = self.FakeResponse(b'binary', 'readable')
        self.assertEqual('readable', root.text('somewhere'))
        self.assertEqual(b'binary', root.read('somewhere'))


class FilterFextRootTestCase(unittest.TestCase):

    def setUp(self):
        self.base = TemporaryDirectory()
        self.root = join(self.base.name, 'root')
        mkdir(self.root)

        with open(join(self.root, 'readme.txt'), 'w') as fd:
            fd.write('text file')

        with open(join(self.root, 'readme.rst'), 'w') as fd:
            fd.write('restructured text file')

        with open(join(self.root, 'readme.md'), 'w') as fd:
            fd.write('markdown file')

    def tearDown(self):
        self.base.cleanup()

    def test_resolution_default(self):
        root = FilterFextRoot(self.root, (
            ('.txt', FilterFextRoot.default),
        ))
        # filename extension will be automatically added
        target = 'readme'
        self.assertEqual('text file', root.text(target))

    def test_resolution_must_have_prefix(self):
        root = FilterFextRoot(self.root, (
            ('txt', FilterFextRoot.default),
        ))
        target = 'readme.'
        # the raw 'txt' suffix, lacking the '.', will be ignored.
        with self.assertRaises(FileNotFoundError):
            root.text(target)

    def test_resolution_order(self):
        def markdown_filter(text):
            return '<p>%s</p>' % text

        # precedence results
        root = FilterFextRoot(self.root, (
            ('.md', markdown_filter),
            ('.txt', FilterFextRoot.default),
        ))
        # filename extension will be automatically added
        target = 'readme'
        self.assertEqual('<p>markdown file</p>', root.text(target))
