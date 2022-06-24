import json
import os
import tempfile
import unittest
from unittest import mock

import coverage
import pytest

import coveralls
from coveralls.api import log


EXPECTED = {
    'message': 'Job #7.1 - 44.58% Covered',
    'url': 'https://coveralls.io/jobs/5869',
}


@mock.patch('coveralls.api.requests')
class WearTest(unittest.TestCase):
    def setUp(self):
        try:
            os.remove('.coverage')
        except Exception:
            pass

    def test_wet_run(self, mock_requests):
        mock_requests.post.return_value.json.return_value = EXPECTED

        result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)
        assert result == EXPECTED

    def test_merge(self, _mock_requests):
        with tempfile.NamedTemporaryFile() as coverage_file:
            coverage_file.write(
                b'{"source_files": [{"name": "foobar", "coverage": []}]}')
            coverage_file.seek(0)

            api = coveralls.Coveralls(repo_token='xxx')
            api.merge(coverage_file.name)
            result = api.create_report()

            source_files = json.loads(result)['source_files']
            assert source_files == [{'name': 'foobar', 'coverage': []}]

    def test_merge_empty_data(self, _mock_requests):
        with tempfile.NamedTemporaryFile() as coverage_file:
            coverage_file.write(b'{}')
            coverage_file.seek(0)

            api = coveralls.Coveralls(repo_token='xxx')
            api.merge(coverage_file.name)
            result = api.create_report()

            source_files = json.loads(result)['source_files']
            assert source_files == []

    @mock.patch.object(log, 'warning')
    def test_merge_invalid_data(self, mock_logger, _mock_requests):
        with tempfile.NamedTemporaryFile() as coverage_file:
            coverage_file.write(b'{"random": "stuff"}')
            coverage_file.seek(0)

            api = coveralls.Coveralls(repo_token='xxx')
            api.merge(coverage_file.name)
            result = api.create_report()

            source_files = json.loads(result)['source_files']
            assert source_files == []

            mock_logger.assert_called_once_with(
                'No data to be merged; does the json file contain '
                '"source_files" data?')

    def test_dry_run(self, mock_requests):
        mock_requests.post.return_value.json.return_value = EXPECTED

        result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=True)
        assert result == {}

    @mock.patch.object(log, 'debug')
    def test_repo_token_in_not_compromised_verbose(self, mock_logger,
                                                   mock_requests):
        mock_requests.post.return_value.json.return_value = EXPECTED

        coveralls.Coveralls(repo_token='xxx').wear(dry_run=True)
        assert 'xxx' not in mock_logger.call_args[0][0]

    def test_coveralls_unavailable(self, mock_requests):
        mock_requests.post.return_value.json.side_effect = ValueError
        mock_requests.post.return_value.status_code = 500
        mock_requests.post.return_value.text = '<html>Http 1./1 500</html>'

        with pytest.raises(coveralls.exception.CoverallsException):
            coveralls.Coveralls(repo_token='xxx').wear()

    @mock.patch('coveralls.reporter.CoverallReporter.report')
    def test_no_coverage(self, report_files, mock_requests):
        mock_requests.post.return_value.json.return_value = EXPECTED
        report_files.side_effect = coverage.CoverageException(
            'No data to report')

        with pytest.raises(coverage.CoverageException):
            coveralls.Coveralls(repo_token='xxx').wear()

    @mock.patch.dict(
        os.environ,
        {'COVERALLS_HOST': 'https://coveralls.my-enterprise.info',
         'COVERALLS_SKIP_SSL_VERIFY': '1'}, clear=True)
    def test_coveralls_host_env_var_overrides_api_url(self, mock_requests):
        coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)
        mock_requests.post.assert_called_once_with(
            'https://coveralls.my-enterprise.info/api/v1/jobs',
            files=mock.ANY, verify=False)

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_api_call_uses_default_host_if_no_env_var_set(self, mock_requests):
        coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)
        mock_requests.post.assert_called_once_with(
            'https://coveralls.io/api/v1/jobs', files=mock.ANY, verify=True)

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_submit_report_resubmission(self, mock_requests):
        # This would trigger the resubmission condition
        mock_requests.post.return_value.status_code = 422
        result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)

        # A new service_job_id is created
        mock_requests.post.return_value.json.return_value = EXPECTED
        result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)

        assert result == EXPECTED

    @mock.patch.dict(
        os.environ,
        {'GITHUB_REPOSITORY': 'test/repo'},
        clear=True)
    def test_submit_report_resubmission_github(self, mock_requests):
        # This would trigger the resubmission condition, for github
        mock_requests.post.return_value.status_code = 422
        result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)

        # A new service_job_id is created, null for github
        mock_requests.post.return_value.json.return_value = EXPECTED
        result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)

        assert result == EXPECTED
