import os
import tempfile
import unittest
from os.path import join as jp, dirname
from pprint import pprint
from subprocess import check_call

from coveralls import Coveralls

COVERAGE_CONFIG = """
[run]
branch = True
data_file = %s

[paths]
source = %s 
 %s
"""

COVERAGE_CODE_STANZA = """
import sys

sys.path.append(%r)

exec('''
import foo

foo.test_func(%r)
''')
"""

COVERAGE_TEMPLATE_PATH = jp(dirname(__file__), "coverage_templates")


class IntegrationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.old_cwd = os.getcwd()
        except FileNotFoundError:
            cls.old_cwd = None

    @classmethod
    def tearDownClass(cls):
        if cls.old_cwd:
            os.chdir(cls.old_cwd)

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        os.chdir(self.temp_dir.name)
        self.covrc = jp(self.temp_dir.name, ".coveragerc")
        self.cov = jp(self.temp_dir.name, ".coverage")
        self.test_file = jp(self.temp_dir.name, "test.py")

    def tearDown(self):
        self.temp_dir.cleanup()

    def _test_harness(self, code):
        with open(self.covrc, "wt") as f:
            f.write(COVERAGE_CONFIG % (self.cov, COVERAGE_TEMPLATE_PATH, self.temp_dir))
        with open(self.test_file, "wt") as f:
            f.write(code)

        check_call(["coverage", "run", "test.py"])

        os.unlink(self.test_file)

        coverallz = Coveralls(repo_token="xxx",
                              config_file=self.covrc)
        report = coverallz.create_data()
        coverallz.create_report()  # This is purely for coverage

        source_files = set(f["name"] for f in report["source_files"])
        self.assertNotIn(self.test_file, source_files)
        self.assertIn(jp(COVERAGE_TEMPLATE_PATH, "foo.py"), source_files)
        self.assertTrue(jp(COVERAGE_TEMPLATE_PATH, "bar.py") in source_files or
                        jp(COVERAGE_TEMPLATE_PATH, "bar_310.py") in source_files)
        self.assertFalse(jp(COVERAGE_TEMPLATE_PATH, "bar.py") in source_files and
                         jp(COVERAGE_TEMPLATE_PATH, "bar_310.py") in source_files)

    def _test_number(self, num):
        self._test_harness(COVERAGE_CODE_STANZA % (COVERAGE_TEMPLATE_PATH, num))

    def test_5(self):
        self._test_number(5)

    def test_7(self):
        self._test_number(7)

    def test_11(self):
        self._test_number(11)
