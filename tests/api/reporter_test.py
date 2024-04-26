import os
import subprocess
import unittest

import pytest

from coveralls import Coveralls
from coveralls.exception import CoverallsException


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
EXAMPLE_DIR = os.path.join(BASE_DIR, 'example')


def assert_coverage(actual, expected):
    assert actual['source'].strip() == expected['source'].strip()
    assert actual['name'] == expected['name']
    assert actual['coverage'] == expected['coverage']
    assert actual.get('branches') == expected.get('branches')


class ReporterTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_cwd = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.old_cwd)

    def setUp(self):
        os.chdir(EXAMPLE_DIR)

        try:
            os.remove('.coverage')
        except Exception:
            pass
        try:
            os.remove('extra.py')
        except Exception:
            pass

    @staticmethod
    def make_test_results(with_branches=False, name_prefix=''):
        results = (
            {
            'source': (
                'def hello():\n'
                '    print(\'world\')\n\n\n'
                'class Foo:\n'
                '    """ Bar """\n\n\n'
                'def baz():\n'
                '    print(\'this is not tested\')\n\n'
                'def branch(cond1, cond2):\n'
                '    if cond1:\n'
                '        print(\'condition tested both ways\')\n'
                '    if cond2:\n'
                '        print(\'condition not tested both ways\')\n'
            ),
            'name': f'{name_prefix}project.py',
            'coverage': [
                1, 1, None, None, 1, None, None,
                None, 1, 0, None, 1, 1, 1, 1, 1,
            ],
            }, {
            'source': (
                'from project import branch\n'
                'from project import hello\n\n'
                "if __name__ == '__main__':\n"
                '    hello()\n'
                '    branch(False, True)\n'
                '    branch(True, True)\n'
            ),
            'name': f'{name_prefix}runtests.py',
            'coverage': [1, 1, None, 1, 1, 1, 1],
            },
        )
        if with_branches:
            results[0]['branches'] = [
                13, 0, 14, 1, 13, 0, 15, 1, 15, 0, 16, 1,
                15, 0, 12, 0,
            ]
            results[1]['branches'] = [4, 0, 5, 1, 4, 0, 1, 0]
        return results

    def test_reporter(self):
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'runtests.py',
            ], cwd=EXAMPLE_DIR,
        )
        results = Coveralls(repo_token='xxx').get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results()
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_no_base_dir_arg(self):
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'example/runtests.py',
            ], cwd=BASE_DIR,
        )

        # without base_dir arg, file name is prefixed with 'example/'
        os.chdir(BASE_DIR)
        results = Coveralls(repo_token='xxx').get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results(name_prefix='example/')
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_with_base_dir_arg(self):
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'example/runtests.py',
            ], cwd=BASE_DIR,
        )

        # without base_dir arg, file name is prefixed with 'example/'
        os.chdir(BASE_DIR)
        results = Coveralls(
            repo_token='xxx',
            base_dir='example',
        ).get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results()
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_with_base_dir_trailing_sep(self):
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'example/runtests.py',
            ], cwd=BASE_DIR,
        )

        # without base_dir arg, file name is prefixed with 'example/'
        os.chdir(BASE_DIR)
        results = Coveralls(
            repo_token='xxx',
            base_dir='example/',
        ).get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results()
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_with_src_dir_arg(self):
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'example/runtests.py',
            ], cwd=BASE_DIR,
        )

        # without base_dir arg, file name is prefixed with 'example/'
        os.chdir(BASE_DIR)
        results = Coveralls(
            repo_token='xxx',
            src_dir='src',
        ).get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results(name_prefix='src/example/')
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_with_src_dir_trailing_sep(self):
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'example/runtests.py',
            ], cwd=BASE_DIR,
        )

        # without base_dir arg, file name is prefixed with 'example/'
        os.chdir(BASE_DIR)
        results = Coveralls(
            repo_token='xxx',
            src_dir='src/',
        ).get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results(name_prefix='src/example/')
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_with_both_base_dir_and_src_dir_args(self):
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'example/runtests.py',
            ], cwd=BASE_DIR,
        )

        # without base_dir arg, file name is prefixed with 'example/'
        os.chdir(BASE_DIR)
        results = Coveralls(
            repo_token='xxx',
            base_dir='example',
            src_dir='src',
        ).get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results(name_prefix='src/')
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_with_branches(self):
        subprocess.call(
            [
                'coverage', 'run', '--branch', '--omit=**/.tox/*',
                'runtests.py',
            ], cwd=EXAMPLE_DIR,
        )
        results = Coveralls(repo_token='xxx').get_coverage()
        assert len(results) == 2

        # Branches are expressed as four values each in a flat list
        assert not len(results[0]['branches']) % 4
        assert not len(results[1]['branches']) % 4

        expected_results = self.make_test_results(with_branches=True)
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_missing_file(self):
        with open('extra.py', 'w') as f:
            f.write('print("Python rocks!")\n')
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'extra.py',
            ], cwd=EXAMPLE_DIR,
        )
        try:
            os.remove('extra.py')
        except Exception:
            pass

        with pytest.raises(CoverallsException, match='No source for code'):
            Coveralls(repo_token='xxx').get_coverage()

    def test_not_python(self):
        with open('extra.py', 'w') as f:
            f.write('print("Python rocks!")\n')
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'extra.py',
            ], cwd=EXAMPLE_DIR,
        )
        with open('extra.py', 'w') as f:
            f.write("<h1>This isn't python!</h1>\n")

        with pytest.raises(
                CoverallsException,
                match=r"Couldn't parse .* as Python",
        ):
            Coveralls(repo_token='xxx').get_coverage()
