import os
import subprocess
import sys
import tempfile
import unittest

from coveralls import Coveralls


COVERAGE_CODE_STANZA = """
import sys
sys.path.append('{}')

import foo
foo.test_func({:d})
"""

COVERAGE_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'data')


class IntegrationTest(unittest.TestCase):
    gitinfo = {
        'GIT_ID': 'asdf1234',
        'GIT_AUTHOR_NAME': 'Integration Tests',
        'GIT_AUTHOR_EMAIL': 'integration@test.com',
        'GIT_COMMITTER_NAME': 'Integration Tests',
        'GIT_COMMITTER_EMAIL': 'integration@test.com',
        'GIT_MESSAGE': 'Ran the integration tests',
    }

    @classmethod
    def setUpClass(cls):
        cls.old_cwd = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.old_cwd)

    def _test_harness(self, num, hits):
        with tempfile.TemporaryDirectory() as tempdir:
            os.chdir(tempdir)

            test_file = os.path.join(tempdir, 'test.py')
            with open(test_file, 'wt') as f:
                f.write(COVERAGE_CODE_STANZA.format(COVERAGE_TEMPLATE_PATH,
                                                    num))

            subprocess.check_call([sys.executable, '-m', 'coverage', 'run',
                                   test_file])

            coverallz = Coveralls(repo_token='xxx')
            report = coverallz.create_data()
            coverallz.create_report()  # This is purely for coverage

            source_files = {f['name'] for f in report['source_files']}
            print(source_files)
            foo = os.path.join(COVERAGE_TEMPLATE_PATH, 'foo.py')
            self.assertIn(foo, source_files)

            lines = next((f['coverage'] for f in report['source_files']
                          if f['name'] == foo), None)
            assert sum(int(bool(x)) for x in lines) == hits

    @unittest.mock.patch.dict(os.environ, gitinfo, clear=True)
    def test_5(self):
        self._test_harness(5, 8)

    @unittest.mock.patch.dict(os.environ, gitinfo, clear=True)
    def test_7(self):
        self._test_harness(7, 9)

    @unittest.mock.patch.dict(os.environ, gitinfo, clear=True)
    def test_11(self):
        self._test_harness(11, 9)
