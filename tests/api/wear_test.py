# coding: utf-8
from __future__ import unicode_literals

import json
import tempfile
import unittest

import coverage
import mock
import sh

from coveralls import Coveralls
from coveralls.api import log


EXPECTED = {'url': 'https://coveralls.io/jobs/5869',
            'message': 'Job #7.1 - 44.58% Covered'}


@mock.patch('coveralls.api.requests')
class WearTest(unittest.TestCase):
    def setUp(self):
        sh.rm('-f', '.coverage')

    def test_wet_run(self, mock_requests):
        mock_requests.post.return_value.json.return_value = EXPECTED

        result = Coveralls(repo_token='xxx').wear(dry_run=False)
        assert result == EXPECTED

    def test_merge(self):
        coverage_file = tempfile.NamedTemporaryFile()
        coverage_file.write(
            b'{"source_files": [{"name": "foobar", "coverage": []}]}')
        coverage_file.seek(0)

        api = Coveralls(repo_token='xxx')
        api.merge(coverage_file.name)
        result = api.create_report()
        result_source = json.loads(result)['source_files']
        assert result_source == [{'name': 'foobar', 'coverage': []}]

    def test_merge_empty_data(self):
        coverage_file = tempfile.NamedTemporaryFile()
        coverage_file.write(b'{}')
        coverage_file.seek(0)

        api = Coveralls(repo_token='xxx')
        api.merge(coverage_file.name)
        result = api.create_report()
        assert json.loads(result)['source_files'] == []

    @mock.patch.object(log, 'warning')
    def test_merge_invalid_data(self, mock_logger):
        coverage_file = tempfile.NamedTemporaryFile()
        coverage_file.write(b'{"random": "stuff"}')
        coverage_file.seek(0)

        api = Coveralls(repo_token='xxx')
        api.merge(coverage_file.name)
        result = api.create_report()
        assert json.loads(result)['source_files'] == []

        mock_logger.assert_called_once_with('No data to be merged; does the '
                                            'json file contain "source_files" '
                                            'data?')

    def test_dry_run(self, mock_requests):
        mock_requests.post.return_value.json.return_value = EXPECTED

        result = Coveralls(repo_token='xxx').wear(dry_run=True)
        assert result == {}

    @mock.patch.object(log, 'debug')
    def test_repo_token_in_not_compromised_verbose(self, mock_logger,
                                                   mock_requests):
        mock_requests.post.return_value.json.return_value = EXPECTED

        Coveralls(repo_token='xxx').wear(dry_run=True)
        assert 'xxx' not in mock_logger.call_args[0][0]

    def test_coveralls_unavailable(self, mock_requests):
        mock_requests.post.return_value.json.side_effect = ValueError
        mock_requests.post.return_value.status_code = 500
        mock_requests.post.return_value.text = '<html>Http 1./1 500</html>'

        result = Coveralls(repo_token='xxx').wear()
        assert result == {
            'message': ('Failure to submit data. Response [500]: '
                        '<html>Http 1./1 500</html>')}

    @mock.patch('coveralls.reporter.CoverallReporter.report')
    def test_no_coverage(self, report_files, mock_requests):
        report_files.side_effect = coverage.CoverageException(
            'No data to report')
        mock_requests.post.return_value.json.return_value = EXPECTED

        result = Coveralls(repo_token='xxx').wear()
        assert result == {
            'message': 'Failure to gather coverage: No data to report'}
