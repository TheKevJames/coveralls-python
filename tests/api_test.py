# coding: utf-8
from __future__ import unicode_literals

import json
import logging
import os
import sys
import tempfile
import unittest

import coverage
import mock
import pytest
import sh

from coveralls import Coveralls
from coveralls.api import log


def assert_coverage(actual, expected):
    assert actual['source'].strip() == expected['source'].strip()
    assert actual['name'] == expected['name']
    assert actual['coverage'] == expected['coverage']
    assert actual.get('branches') == expected.get('branches')


class ReporterTest(unittest.TestCase):

    def setUp(self):
        os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'example'))
        sh.rm('-f', '.coverage')
        sh.rm('-f', 'extra.py')
        self.cover = Coveralls(repo_token='xxx')

    def test_reporter(self):
        sh.coverage('run', 'runtests.py')
        results = self.cover.get_coverage()
        assert len(results) == 2
        assert_coverage({
            'source': '# coding: utf-8\n\n\ndef hello():\n    print(\'world\')\n\n\nclass Foo(object):\n    """ Bar """\n\n\ndef baz():\n    print(\'this is not tested\')\n\ndef branch(cond1, cond2):\n    if cond1:\n        print(\'condition tested both ways\')\n    if cond2:\n        print(\'condition not tested both ways\')',
            'name': 'project.py',
            'coverage': [None, None, None, 1, 1, None, None, 1, None, None, None, 1, 0, None, 1, 1, 1, 1, 1]}, results[0])
        assert_coverage({
            'source': "# coding: utf-8\nfrom project import hello, branch\n\nif __name__ == '__main__':\n    hello()\n    branch(False, True)\n    branch(True, True)",
            'name': 'runtests.py', 'coverage': [None, 1, None, 1, 1, 1, 1]}, results[1])

    def test_reporter_with_branches(self):
        sh.coverage('run', '--branch', 'runtests.py')
        results = self.cover.get_coverage()
        assert len(results) == 2

        # Branches are expressed as four values each in a flat list
        assert not len(results[0]['branches']) % 4
        assert not len(results[1]['branches']) % 4

        assert_coverage({
            'source': '# coding: utf-8\n\n\ndef hello():\n    print(\'world\')\n\n\nclass Foo(object):\n    """ Bar """\n\n\ndef baz():\n    print(\'this is not tested\')\n\ndef branch(cond1, cond2):\n    if cond1:\n        print(\'condition tested both ways\')\n    if cond2:\n        print(\'condition not tested both ways\')',
            'name': 'project.py',
            'branches': [16, 0, 17, 1, 16, 0, 18, 1, 18, 0, 19, 1, 18, 0, 15, 0],
            'coverage': [None, None, None, 1, 1, None, None, 1, None, None, None, 1, 0, None, 1, 1, 1, 1, 1]}, results[0])
        assert_coverage({
            'source': "# coding: utf-8\nfrom project import hello, branch\n\nif __name__ == '__main__':\n    hello()\n    branch(False, True)\n    branch(True, True)",
            'name': 'runtests.py',
            'branches': [4, 0, 5, 1, 4, 0, 2, 0],
            'coverage': [None, 1, None, 1, 1, 1, 1]}, results[1])

    def test_missing_file(self):
        sh.echo('print("Python rocks!")', _out='extra.py')
        sh.coverage('run', 'extra.py')
        sh.rm('-f', 'extra.py')
        assert self.cover.get_coverage() == []

    def test_not_python(self):
        sh.echo('print("Python rocks!")', _out='extra.py')
        sh.coverage('run', 'extra.py')
        sh.echo("<h1>This isn't python!</h1>", _out='extra.py')
        assert self.cover.get_coverage() == []


def test_non_unicode():
    os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nonunicode'))
    sh.coverage('run', 'nonunicode.py')
    expected_json_part = '"source": "# coding: iso-8859-15\\n\\ndef hello():\\n    print(\'I like P\\u00f3lya distribution.\')'
    assert expected_json_part in json.dumps(Coveralls(repo_token='xxx').get_coverage())


@pytest.mark.skipif(sys.version_info >= (3, 0), reason='python 3 not affected')
@pytest.mark.skipif(coverage.__version__.startswith('4.'), reason='coverage 4 not affected')
def test_malformed_encoding_declaration(capfd):
    os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nonunicode'))
    sh.coverage('run', 'malformed.py')
    logging.getLogger('coveralls').addHandler(logging.StreamHandler())
    result_object = Coveralls(repo_token='xxx').get_coverage()
    assert result_object == []
    _, err = capfd.readouterr()
    assert 'Source file malformed.py can not be properly decoded' in err


@pytest.mark.skipif(sys.version_info < (3, 0) or coverage.__version__.startswith('3.'),
                    reason='python 2 or coverage 3 fail')
def test_malformed_encoding_declaration_py3_or_coverage4():
    os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nonunicode'))
    sh.coverage('run', 'malformed.py')
    logging.getLogger('coveralls').addHandler(logging.StreamHandler())
    result_object = Coveralls(repo_token='xxx').get_coverage()
    assert len(result_object) == 1
    assert_coverage({'coverage': [None, None, 1, 0], 'name': 'malformed.py',
                     'source': '# -*- cоding: utf-8 -*-\n\ndef hello():\n    return 1\n'},
                    result_object[0])


@mock.patch('coveralls.api.requests')
class WearTest(unittest.TestCase):

    def setUp(self):
        sh.rm('-f', '.coverage')
        self.expected_json = {'url': 'https://coveralls.io/jobs/5869', 'message': 'Job #7.1 - 44.58% Covered'}

    def setup_mock(self, mock_requests):
        mock_requests.post.return_value.json.return_value = self.expected_json

    def test_wet_run(self, mock_requests):
        self.setup_mock(mock_requests)
        result = Coveralls(repo_token='xxx').wear(dry_run=False)
        assert result == self.expected_json

    def test_merge(self, _mock_requests):
        api = Coveralls(repo_token='xxx')
        coverage_file = tempfile.NamedTemporaryFile()
        coverage_file.write(b'{"source_files": [{"name": "foobar", "coverage": []}]}')
        coverage_file.seek(0)
        api.merge(coverage_file.name)
        result = api.create_report()
        assert json.loads(result)['source_files'] == [{'name': 'foobar', 'coverage': []}]

    def test_merge_empty_data(self, _mock_requests):
        api = Coveralls(repo_token='xxx')
        coverage_file = tempfile.NamedTemporaryFile()
        coverage_file.write(b'{}')
        coverage_file.seek(0)
        api.merge(coverage_file.name)
        result = api.create_report()
        assert json.loads(result)['source_files'] == []

    @mock.patch.object(log, 'warning')
    def test_merge_invalid_data(self, mock_logger, _mock_requests):
        api = Coveralls(repo_token='xxx')
        coverage_file = tempfile.NamedTemporaryFile()
        coverage_file.write(b'{"random": "stuff"}')
        coverage_file.seek(0)
        api.merge(coverage_file.name)
        result = api.create_report()
        assert json.loads(result)['source_files'] == []
        mock_logger.assert_called_once_with('No data to be merged; does the '
                                            'json file contain "source_files" data?')

    def test_dry_run(self, mock_requests):
        self.setup_mock(mock_requests)
        result = Coveralls(repo_token='xxx').wear(dry_run=True)
        assert result == {}

    @mock.patch.object(log, 'debug')
    def test_repo_token_in_not_compromised_verbose(self, mock_logger, mock_requests):
        self.setup_mock(mock_requests)
        Coveralls(repo_token='xxx').wear(dry_run=True)
        assert 'xxx' not in mock_logger.call_args[0][0]

    def test_coveralls_unavailable(self, mock_requests):
        mock_requests.post.return_value.json.side_effect = ValueError
        mock_requests.post.return_value.status_code = 500
        mock_requests.post.return_value.text = '<html>Http 1./1 500</html>'
        result = Coveralls(repo_token='xxx').wear()
        assert result == {'message': 'Failure to submit data. Response [500]: <html>Http 1./1 500</html>'}

    @mock.patch('coveralls.reporter.CoverallReporter.report')
    def test_no_coverage(self, report_files, mock_requests):
        report_files.side_effect = coverage.CoverageException('No data to report')
        self.setup_mock(mock_requests)
        result = Coveralls(repo_token='xxx').wear()
        assert result == {'message': 'Failure to gather coverage: No data to report'}


def test_output_to_file(tmpdir):
    """Check we can write coveralls report into the file."""

    test_log = tmpdir.join('test.log')
    Coveralls(repo_token='xxx').save_report(test_log.strpath)
    report = test_log.read()
    assert json.loads(report)['repo_token'] == 'xxx'
