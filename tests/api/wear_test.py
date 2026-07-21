import contextlib
import json
import os
import pathlib
import tempfile
import unittest.mock

import coverage
import pytest
import requests

import coveralls
from coveralls.api import log


EXPECTED = {
    'message': 'Job #7.1 - 44.58% Covered',
    'url': 'https://coveralls.io/jobs/5869',
}


@unittest.mock.patch('coveralls.api.requests')
class WearTest(unittest.TestCase):
    def setUp(self):
        with contextlib.suppress(Exception):
            pathlib.Path('.coverage').unlink()

    def test_wet_run(self, mock_requests):
        mock_requests.post.return_value.json.return_value = EXPECTED

        result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)
        assert result == EXPECTED

    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_client_settings_do_not_leak_into_payload(self, _mock_requests):
        # Regression guard at the create_data() boundary: base_dir/src_dir/
        # rcfile and the timeout family are client-only and must never enter
        # the submitted JSON.
        api = coveralls.Coveralls(
            repo_token='xxx',
            service_name='travis-ci',
            base_dir='foo',
            src_dir='bar',
            rcfile='.coveragerc',
            timeout=30,
            connect_timeout=5,
            read_timeout=25,
        )
        with unittest.mock.patch.object(api, 'get_coverage', return_value=[]):
            data = api.create_data()

        for leaked in (
            'base_dir', 'src_dir', 'rcfile', 'config_file',
            'timeout', 'connect_timeout', 'read_timeout',
        ):
            assert leaked not in data
        assert data['repo_token'] == 'xxx'
        assert data['service_name'] == 'travis-ci'

    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_set_payload_fields_are_forwarded_including_falsey(
        self, _mock_requests,
    ):
        # Every job field the API accepts is forwarded when set -- including
        # run_at, and including explicitly-falsey values (parallel=False, a
        # numeric 0 job id). Only genuinely-absent fields are dropped.
        api = coveralls.Coveralls(
            repo_token='xxx',
            service_name='travis-ci',
            run_at='2013-02-18 00:52:48 -0800',
            parallel=False,
            service_job_id=0,
        )
        with unittest.mock.patch.object(api, 'get_coverage', return_value=[]):
            data = api.create_data()

        assert data['run_at'] == '2013-02-18 00:52:48 -0800'
        assert data['parallel'] is False
        assert data['service_job_id'] == 0

    def test_merge(self, _mock_requests):
        with tempfile.NamedTemporaryFile() as coverage_file:
            coverage_file.write(
                b'{"source_files": [{"name": "foobar", "coverage": []}]}',
            )
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

    def test_merge_invalid_data(self, _mock_requests):
        with tempfile.NamedTemporaryFile() as coverage_file:
            coverage_file.write(b'{"random": "stuff"}')
            coverage_file.seek(0)

            with unittest.mock.patch.object(log, 'warning') as logger:
                api = coveralls.Coveralls(repo_token='xxx')
                api.merge(coverage_file.name)
                result = api.create_report()

            source_files = json.loads(result)['source_files']
            assert source_files == []

            logger.assert_called_once_with(
                'No data to be merged; does the json file contain '
                '"source_files" data?',
            )

    def test_dry_run(self, mock_requests):
        mock_requests.post.return_value.json.return_value = EXPECTED

        result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=True)
        assert result == {}

    def test_repo_token_in_not_compromised_verbose(self, mock_requests):
        mock_requests.post.return_value.json.return_value = EXPECTED

        with unittest.mock.patch.object(log, 'debug') as logger:
            coveralls.Coveralls(repo_token='xxx').wear(dry_run=True)

        assert 'xxx' not in logger.call_args[0][0]

    def test_coveralls_unavailable(self, mock_requests):
        mock_requests.post.return_value.json.side_effect = ValueError
        mock_requests.post.return_value.status_code = 500
        mock_requests.post.return_value.text = '<html>Http 1./1 500</html>'

        with pytest.raises(RuntimeError):
            coveralls.Coveralls(repo_token='xxx').wear()

    @unittest.mock.patch('coveralls.reporter.CoverallReporter.report')
    def test_no_coverage(self, report_files, mock_requests):
        mock_requests.post.return_value.json.return_value = EXPECTED
        report_files.side_effect = coverage.CoverageException(
            'No data to report',
        )

        with pytest.raises(coverage.CoverageException):
            coveralls.Coveralls(repo_token='xxx').wear()

    @unittest.mock.patch.dict(
        os.environ,
        {
            'COVERALLS_HOST': 'https://coveralls.my-enterprise.info',
            'COVERALLS_SKIP_SSL_VERIFY': '1',
        }, clear=True,
    )
    def test_coveralls_host_env_var_overrides_api_url(self, mock_requests):
        coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)
        mock_requests.post.assert_called_once_with(
            'https://coveralls.my-enterprise.info/api/v1/jobs',
            files=unittest.mock.ANY, verify=False, timeout=(10, 60),
        )

    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_host_and_skip_ssl_verify_via_override(self, mock_requests):
        # host/skip_ssl_verify are first-class Config fields, settable through
        # any channel -- here as explicit overrides, not just env vars.
        coveralls.Coveralls(
            repo_token='xxx',
            host='https://coveralls.my-enterprise.info',
            skip_ssl_verify=True,
        ).wear(dry_run=False)
        mock_requests.post.assert_called_once_with(
            'https://coveralls.my-enterprise.info/api/v1/jobs',
            files=unittest.mock.ANY, verify=False, timeout=(10, 60),
        )

    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_api_call_uses_default_host_if_no_env_var_set(self, mock_requests):
        coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)
        mock_requests.post.assert_called_once_with(
            'https://coveralls.io/api/v1/jobs',
            files=unittest.mock.ANY,
            verify=True,
            timeout=(10, 60),
        )

    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_submit_report_uses_default_timeout(self, mock_requests):
        mock_requests.post.return_value.json.return_value = EXPECTED
        coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)
        _, kwargs = mock_requests.post.call_args
        assert kwargs['timeout'] == (10, 60)

    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_submit_report_raises_on_timeout(self, mock_requests):
        mock_requests.exceptions.Timeout = requests.exceptions.Timeout
        mock_requests.post.side_effect = requests.exceptions.Timeout('boom')
        with pytest.raises(
            TimeoutError,
            match=r'Timed out submitting coverage',
        ):
            coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)

    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_parallel_finish_uses_default_timeout(self, mock_requests):
        mock_requests.post.return_value.json.return_value = {'done': True}
        coveralls.Coveralls(repo_token='xxx').parallel_finish()
        _, kwargs = mock_requests.post.call_args
        assert kwargs['timeout'] == (10, 60)

    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_parallel_finish_raises_on_timeout(self, mock_requests):
        mock_requests.exceptions.Timeout = requests.exceptions.Timeout
        mock_requests.post.side_effect = requests.exceptions.Timeout('boom')
        with pytest.raises(
            TimeoutError,
            match=r'Timed out finishing parallel jobs',
        ):
            coveralls.Coveralls(repo_token='xxx').parallel_finish()

    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_submit_report_resubmission(self, mock_requests):
        # This would trigger the resubmission condition
        mock_requests.post.return_value.status_code = 422
        result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)

        # A new service_job_id is created
        mock_requests.post.return_value.json.return_value = EXPECTED
        result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)

        assert result == EXPECTED

    @unittest.mock.patch.dict(
        os.environ,
        {'GITHUB_REPOSITORY': 'test/repo'},
        clear=True,
    )
    def test_submit_report_resubmission_github(self, mock_requests):
        # This would trigger the resubmission condition, for github
        mock_requests.post.return_value.status_code = 422
        result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)

        # A new service_job_id is created, null for github
        mock_requests.post.return_value.json.return_value = EXPECTED
        result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)

        assert result == EXPECTED
