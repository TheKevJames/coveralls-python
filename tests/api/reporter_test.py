# pylint: disable=no-self-use
import os
import subprocess
import unittest

from coveralls import Coveralls


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
EXAMPLE_DIR = os.path.join(BASE_DIR, 'example')


def assert_coverage(actual, expected):
    assert actual['source'].strip() == expected['source'].strip()
    assert actual['name'] == expected['name']
    assert actual['coverage'] == expected['coverage']
    assert actual.get('branches') == expected.get('branches')


class ReporterTest(unittest.TestCase):
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

    def test_reporter(self):
        subprocess.call(['coverage', 'run', '--omit=**/.tox/*',
                         'runtests.py'], cwd=EXAMPLE_DIR)
        results = Coveralls(repo_token='xxx').get_coverage()
        assert len(results) == 2

        assert_coverage(results[0], {
            'source': ('def hello():\n'
                       '    print(\'world\')\n\n\n'
                       'class Foo:\n'
                       '    """ Bar """\n\n\n'
                       'def baz():\n'
                       '    print(\'this is not tested\')\n\n'
                       'def branch(cond1, cond2):\n'
                       '    if cond1:\n'
                       '        print(\'condition tested both ways\')\n'
                       '    if cond2:\n'
                       '        print(\'condition not tested both ways\')\n'),
            'name': 'project.py',
            'coverage': [1, 1, None, None, 1, None, None,
                         None, 1, 0, None, 1, 1, 1, 1, 1]})

        assert_coverage(results[1], {
            'source': ('from project import branch\n'
                       'from project import hello\n\n'
                       "if __name__ == '__main__':\n"
                       '    hello()\n'
                       '    branch(False, True)\n'
                       '    branch(True, True)\n'),
            'name': 'runtests.py',
            'coverage': [1, 1, None, 1, 1, 1, 1]})

    def test_reporter_no_base_dir_arg(self):
        subprocess.call(['coverage', 'run', '--omit=**/.tox/*',
                         'example/runtests.py'], cwd=BASE_DIR)

        # without base_dir arg, file name is prefixed with 'example/'
        os.chdir(BASE_DIR)
        results = Coveralls(repo_token='xxx').get_coverage()
        assert len(results) == 2

        assert_coverage(results[0], {
            'source': ('def hello():\n'
                       '    print(\'world\')\n\n\n'
                       'class Foo:\n'
                       '    """ Bar """\n\n\n'
                       'def baz():\n'
                       '    print(\'this is not tested\')\n\n'
                       'def branch(cond1, cond2):\n'
                       '    if cond1:\n'
                       '        print(\'condition tested both ways\')\n'
                       '    if cond2:\n'
                       '        print(\'condition not tested both ways\')\n'),
            'name': 'example/project.py',
            'coverage': [1, 1, None, None, 1, None, None,
                         None, 1, 0, None, 1, 1, 1, 1, 1]})

        assert_coverage(results[1], {
            'source': ('from project import branch\n'
                       'from project import hello\n\n'
                       "if __name__ == '__main__':\n"
                       '    hello()\n'
                       '    branch(False, True)\n'
                       '    branch(True, True)\n'),
            'name': 'example/runtests.py',
            'coverage': [1, 1, None, 1, 1, 1, 1]})

    def test_reporter_with_base_dir_arg(self):
        subprocess.call(['coverage', 'run', '--omit=**/.tox/*',
                         'example/runtests.py'], cwd=BASE_DIR)

        # without base_dir arg, file name is prefixed with 'example/'
        os.chdir(BASE_DIR)
        results = Coveralls(repo_token='xxx',
                            base_dir='example').get_coverage()
        assert len(results) == 2

        assert_coverage(results[0], {
            'source': ('def hello():\n'
                       '    print(\'world\')\n\n\n'
                       'class Foo:\n'
                       '    """ Bar """\n\n\n'
                       'def baz():\n'
                       '    print(\'this is not tested\')\n\n'
                       'def branch(cond1, cond2):\n'
                       '    if cond1:\n'
                       '        print(\'condition tested both ways\')\n'
                       '    if cond2:\n'
                       '        print(\'condition not tested both ways\')\n'),
            'name': 'project.py',
            'coverage': [1, 1, None, None, 1, None, None,
                         None, 1, 0, None, 1, 1, 1, 1, 1]})

        assert_coverage(results[1], {
            'source': ('from project import branch\n'
                       'from project import hello\n\n'
                       "if __name__ == '__main__':\n"
                       '    hello()\n'
                       '    branch(False, True)\n'
                       '    branch(True, True)\n'),
            'name': 'runtests.py',
            'coverage': [1, 1, None, 1, 1, 1, 1]})

    def test_reporter_with_base_dir_trailing_sep(self):
        subprocess.call(['coverage', 'run', '--omit=**/.tox/*',
                         'example/runtests.py'], cwd=BASE_DIR)

        # without base_dir arg, file name is prefixed with 'example/'
        os.chdir(BASE_DIR)
        results = Coveralls(repo_token='xxx',
                            base_dir='example/').get_coverage()
        assert len(results) == 2

        assert_coverage(results[0], {
            'source': ('def hello():\n'
                       '    print(\'world\')\n\n\n'
                       'class Foo:\n'
                       '    """ Bar """\n\n\n'
                       'def baz():\n'
                       '    print(\'this is not tested\')\n\n'
                       'def branch(cond1, cond2):\n'
                       '    if cond1:\n'
                       '        print(\'condition tested both ways\')\n'
                       '    if cond2:\n'
                       '        print(\'condition not tested both ways\')\n'),
            'name': 'project.py',
            'coverage': [1, 1, None, None, 1, None, None,
                         None, 1, 0, None, 1, 1, 1, 1, 1]})

        assert_coverage(results[1], {
            'source': ('from project import branch\n'
                       'from project import hello\n\n'
                       "if __name__ == '__main__':\n"
                       '    hello()\n'
                       '    branch(False, True)\n'
                       '    branch(True, True)\n'),
            'name': 'runtests.py',
            'coverage': [1, 1, None, 1, 1, 1, 1]})

    def test_reporter_with_branches(self):
        subprocess.call(['coverage', 'run', '--branch', '--omit=**/.tox/*',
                         'runtests.py'], cwd=EXAMPLE_DIR)
        results = Coveralls(repo_token='xxx').get_coverage()
        assert len(results) == 2

        # Branches are expressed as four values each in a flat list
        assert not len(results[0]['branches']) % 4
        assert not len(results[1]['branches']) % 4

        assert_coverage(results[0], {
            'source': ('def hello():\n'
                       '    print(\'world\')\n\n\n'
                       'class Foo:\n'
                       '    """ Bar """\n\n\n'
                       'def baz():\n'
                       '    print(\'this is not tested\')\n\n'
                       'def branch(cond1, cond2):\n'
                       '    if cond1:\n'
                       '        print(\'condition tested both ways\')\n'
                       '    if cond2:\n'
                       '        print(\'condition not tested both ways\')\n'),
            'name': 'project.py',
            'branches': [13, 0, 14, 1, 13, 0, 15, 1, 15, 0, 16, 1, 15, 0, 12,
                         0],
            'coverage': [1, 1, None, None, 1, None, None,
                         None, 1, 0, None, 1, 1, 1, 1, 1]})

        assert_coverage(results[1], {
            'source': ('from project import branch\n'
                       'from project import hello\n\n'
                       "if __name__ == '__main__':\n"
                       '    hello()\n'
                       '    branch(False, True)\n'
                       '    branch(True, True)\n'),
            'name': 'runtests.py',
            'branches': [4, 0, 5, 1, 4, 0, 1, 0],
            'coverage': [1, 1, None, 1, 1, 1, 1]})

    def test_missing_file(self):
        with open('extra.py', 'w') as f:
            f.write('print("Python rocks!")\n')
        subprocess.call(['coverage', 'run', '--omit=**/.tox/*',
                         'extra.py'], cwd=EXAMPLE_DIR)
        try:
            os.remove('extra.py')
        except Exception:
            pass
        assert Coveralls(repo_token='xxx').get_coverage() == []

    def test_not_python(self):
        with open('extra.py', 'w') as f:
            f.write('print("Python rocks!")\n')
        subprocess.call(['coverage', 'run', '--omit=**/.tox/*',
                         'extra.py'], cwd=EXAMPLE_DIR)
        with open('extra.py', 'w') as f:
            f.write("<h1>This isn't python!</h1>\n")
        assert Coveralls(repo_token='xxx').get_coverage() == []
