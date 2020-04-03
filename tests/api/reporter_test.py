# coding: utf-8
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
            'source': ('# coding: utf-8\n\n\n'
                       'def hello():\n'
                       '    print(\'world\')\n\n\n'
                       'class Foo(object):\n'
                       '    """ Bar """\n\n\n'
                       'def baz():\n'
                       '    print(\'this is not tested\')\n\n'
                       'def branch(cond1, cond2):\n'
                       '    if cond1:\n'
                       '        print(\'condition tested both ways\')\n'
                       '    if cond2:\n'
                       '        print(\'condition not tested both ways\')'),
            'name': 'project.py',
            'coverage': [None, None, None, 1, 1, None, None, 1, None, None,
                         None, 1, 0, None, 1, 1, 1, 1, 1]})

        assert_coverage(results[1], {
            'source': ('# coding: utf-8\n'
                       'from project import hello, branch\n\n'
                       "if __name__ == '__main__':\n"
                       '    hello()\n'
                       '    branch(False, True)\n'
                       '    branch(True, True)'),
            'name': 'runtests.py',
            'coverage': [None, 1, None, 1, 1, 1, 1]})

    def test_reporter_with_branches(self):
        subprocess.call(['coverage', 'run', '--branch', '--omit=**/.tox/*',
                         'runtests.py'], cwd=EXAMPLE_DIR)
        results = Coveralls(repo_token='xxx').get_coverage()
        assert len(results) == 2

        # Branches are expressed as four values each in a flat list
        assert not len(results[0]['branches']) % 4
        assert not len(results[1]['branches']) % 4

        assert_coverage(results[0], {
            'source': ('# coding: utf-8\n\n\n'
                       'def hello():\n'
                       '    print(\'world\')\n\n\n'
                       'class Foo(object):\n'
                       '    """ Bar """\n\n\n'
                       'def baz():\n'
                       '    print(\'this is not tested\')\n\n'
                       'def branch(cond1, cond2):\n'
                       '    if cond1:\n'
                       '        print(\'condition tested both ways\')\n'
                       '    if cond2:\n'
                       '        print(\'condition not tested both ways\')'),
            'name': 'project.py',
            'branches': [16, 0, 17, 1, 16, 0, 18, 1, 18, 0, 19, 1, 18, 0, 15,
                         0],
            'coverage': [None, None, None, 1, 1, None, None, 1, None, None,
                         None, 1, 0, None, 1, 1, 1, 1, 1]})

        assert_coverage(results[1], {
            'source': ('# coding: utf-8\n'
                       'from project import hello, branch\n\n'
                       "if __name__ == '__main__':\n"
                       '    hello()\n'
                       '    branch(False, True)\n'
                       '    branch(True, True)'),
            'name': 'runtests.py',
            'branches': [4, 0, 5, 1, 4, 0, 2, 0],
            'coverage': [None, 1, None, 1, 1, 1, 1]})

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
