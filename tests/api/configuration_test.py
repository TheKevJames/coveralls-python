import os
import tempfile
import unittest
from unittest import mock

import pytest
try:
    import yaml
except ImportError:
    yaml = None

from coveralls import Coveralls
from coveralls.api import log


@mock.patch.object(Coveralls, 'config_filename', '.coveralls.mock')
class Configuration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_cwd = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.old_cwd)

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.chdir(self.dir)
        with open('.coveralls.mock', 'w+') as fp:
            fp.write('repo_token: xxx\n')
            fp.write('service_name: jenkins\n')

    @pytest.mark.skipif(yaml is None, reason='requires PyYAML')
    @mock.patch.dict(os.environ, {}, clear=True)
    def test_local_with_config(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'jenkins'
        assert cover.config['repo_token'] == 'xxx'
        assert 'service_job_id' not in cover.config

    @pytest.mark.skipif(yaml is not None, reason='requires no PyYAML')
    @mock.patch.dict(os.environ, {'COVERALLS_REPO_TOKEN': 'xxx'}, clear=True)
    def test_local_with_config_without_yaml_module(self):
        """test local with config in yaml, but without yaml-installed"""
        with mock.patch.object(log, 'warning') as logger:
            cover = Coveralls()

        logger.assert_called_once_with(
            'PyYAML is not installed, skipping %s.', cover.config_filename,
        )


@mock.patch.object(Coveralls, 'config_filename', '.coveralls.mock')
class NoConfiguration(unittest.TestCase):
    @mock.patch.dict(
        os.environ, {
            'TRAVIS': 'True',
            'TRAVIS_JOB_ID': '777',
            'COVERALLS_REPO_TOKEN': 'yyy',
        }, clear=True,
    )
    def test_repo_token_from_env(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'travis-ci'
        assert cover.config['service_job_id'] == '777'
        assert cover.config['repo_token'] == 'yyy'

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_misconfigured(self):
        with pytest.raises(Exception) as excinfo:
            Coveralls()

        assert str(excinfo.value) == (
            'Not on TravisCI. You have to provide either repo_token in '
            '.coveralls.mock or set the COVERALLS_REPO_TOKEN env var.'
        )

    @mock.patch.dict(os.environ, {'GITHUB_ACTIONS': 'true'}, clear=True)
    def test_misconfigured_github(self):
        with pytest.raises(Exception) as excinfo:
            Coveralls()

        assert str(excinfo.value).startswith(
            'Running on Github Actions but GITHUB_TOKEN is not set.',
        )

    @mock.patch.dict(
        os.environ, {
            'APPVEYOR': 'True',
            'APPVEYOR_BUILD_ID': '1234567',
            'APPVEYOR_PULL_REQUEST_NUMBER': '1234',
        },
        clear=True,
    )
    def test_appveyor_no_config(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'appveyor'
        assert cover.config['service_job_id'] == '1234567'
        assert cover.config['service_pull_request'] == '1234'

    @mock.patch.dict(
        os.environ, {
            'BUILDKITE': 'True',
            'BUILDKITE_JOB_ID': '1234567',
            'BUILDKITE_PULL_REQUEST': '1234',
        },
        clear=True,
    )
    def test_buildkite_no_config(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'buildkite'
        assert cover.config['service_job_id'] == '1234567'
        assert cover.config['service_pull_request'] == '1234'

    @mock.patch.dict(
        os.environ, {
            'BUILDKITE': 'True',
            'BUILDKITE_JOB_ID': '1234567',
            'BUILDKITE_PULL_REQUEST': 'false',
        },
        clear=True,
    )
    def test_buildkite_no_config_no_pr(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'buildkite'
        assert cover.config['service_job_id'] == '1234567'
        assert 'service_pull_request' not in cover.config

    @mock.patch.dict(
        os.environ,
        {
            'CIRCLECI': 'True',
            'CIRCLE_BUILD_NUM': '888',
            'CI_PULL_REQUEST': 'https://github.com/org/repo/pull/9999',
        },
        clear=True,
    )
    def test_circleci_singular_no_config(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'circleci'
        assert cover.config['service_number'] == '888'
        assert cover.config['service_pull_request'] == '9999'

    @mock.patch.dict(
        os.environ,
        {
            'CIRCLECI': 'True',
            'CIRCLE_WORKFLOW_ID': '0ea2c0f7-4e56-4a94-bf77-bfae6bdbf80a',
            'CIRCLE_NODE_INDEX': '15',
        },
        clear=True,
    )
    def test_circleci_parallel_no_config(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'circleci'
        assert cover.config['service_number'] == (
            '0ea2c0f7-4e56-4a94-bf77-bfae6bdbf80a'
        )
        assert cover.config['service_job_id'] == '15'

    @mock.patch.dict(
        os.environ,
        {
            'GITHUB_ACTIONS': 'true',
            'GITHUB_REF': 'refs/pull/1234/merge',
            'GITHUB_SHA': 'bb0e00166b28f49db04d6a8b8cb4bddb5afa529f',
            'GITHUB_RUN_ID': '123456789',
            'GITHUB_RUN_NUMBER': '12',
            'GITHUB_HEAD_REF': 'fixup-branch',
            'COVERALLS_REPO_TOKEN': 'xxx',
        },
        clear=True,
    )
    def test_github_no_config(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'github'
        assert cover.config['service_pull_request'] == '1234'
        assert cover.config['service_number'] == '123456789'
        assert cover.config['service_job_id'] == '123456789'

    @mock.patch.dict(
        os.environ,
        {
            'GITHUB_ACTIONS': 'true',
            'GITHUB_TOKEN': 'xxx',
            'GITHUB_REF': 'refs/heads/master',
            'GITHUB_SHA': 'bb0e00166b28f49db04d6a8b8cb4bddb5afa529f',
            'GITHUB_RUN_ID': '987654321',
            'GITHUB_RUN_NUMBER': '21',
            'GITHUB_HEAD_REF': '',
        },
        clear=True,
    )
    def test_github_no_config_no_pr(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'github'
        assert cover.config['service_number'] == '987654321'
        assert cover.config['service_job_id'] == '987654321'
        assert 'service_pull_request' not in cover.config

    @mock.patch.dict(
        os.environ,
        {
            'JENKINS_HOME': '/var/lib/jenkins',
            'BUILD_NUMBER': '888',
            'CI_PULL_REQUEST': 'https://github.com/org/repo/pull/9999',
        },
        clear=True,
    )
    def test_jenkins_no_config(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'jenkins'
        assert cover.config['service_job_id'] == '888'
        assert cover.config['service_pull_request'] == '9999'

    @mock.patch.dict(
        os.environ, {
            'TRAVIS': 'True',
            'TRAVIS_JOB_ID': '777',
        }, clear=True,
    )
    def test_travis_no_config(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'travis-ci'
        assert cover.config['service_job_id'] == '777'
        assert 'repo_token' not in cover.config

    @mock.patch.dict(
        os.environ,
        {
            'SEMAPHORE': 'True',
            'SEMAPHORE_EXECUTABLE_UUID': '36980c73',
            'SEMAPHORE_JOB_UUID': 'a26d42cf',
            'SEMAPHORE_BRANCH_ID': '9999',
        },
        clear=True,
    )
    def test_semaphore_classic_no_config(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'semaphore-ci'
        assert cover.config['service_job_id'] == 'a26d42cf'
        assert cover.config['service_number'] == '36980c73'
        assert cover.config['service_pull_request'] == '9999'

    @mock.patch.dict(
        os.environ,
        {
            'SEMAPHORE': 'True',
            'SEMAPHORE_WORKFLOW_ID': 'b86b3adf',
            'SEMAPHORE_JOB_ID': '2b942b49',
            'SEMAPHORE_GIT_PR_NUMBER': '9999',
        },
        clear=True,
    )
    def test_semaphore_20_no_config(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'semaphore-ci'
        assert cover.config['service_job_id'] == '2b942b49'
        assert cover.config['service_number'] == 'b86b3adf'
        assert cover.config['service_pull_request'] == '9999'

    @mock.patch.dict(
        os.environ,
        {
            'CI_NAME': 'generic-ci',
            'CI_PULL_REQUEST': 'pull/1234',
            'CI_JOB_ID': 'bb0e00166',
            'CI_BUILD_NUMBER': '3',
            'CI_BUILD_URL': 'https://generic-ci.local/build/123456789',
            'CI_BRANCH': 'fixup-branch',
            'COVERALLS_REPO_TOKEN': 'xxx',
        },
        clear=True,
    )
    def test_generic_no_config(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'generic-ci'
        assert cover.config['service_job_id'] == 'bb0e00166'
        assert cover.config['service_branch'] == 'fixup-branch'
        assert cover.config['service_pull_request'] == '1234'

    @mock.patch.dict(
        os.environ,
        {
            'CI_NAME': 'generic-ci',
            'CI_PULL_REQUEST': '',
            'CI_JOB_ID': 'bb0e00166',
            'CI_BUILD_NUMBER': '3',
            'CI_BUILD_URL': 'https://generic-ci.local/build/123456789',
            'CI_BRANCH': 'fixup-branch',
            'COVERALLS_REPO_TOKEN': 'xxx',
        },
        clear=True,
    )
    def test_generic_no_config_no_pr(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'generic-ci'
        assert cover.config['service_job_id'] == 'bb0e00166'
        assert cover.config['service_branch'] == 'fixup-branch'
        assert 'service_pull_request' not in cover.config

    @mock.patch.dict(
        os.environ,
        {
            'COVERALLS_HOST': 'aaa',
            'COVERALLS_PARALLEL': 'true',
            'COVERALLS_REPO_TOKEN': 'a1b2c3d4',
            'COVERALLS_SERVICE_NAME': 'bbb',
            'COVERALLS_FLAG_NAME': 'cc',
            'COVERALLS_SERVICE_JOB_NUMBER': '1234',
        },
        clear=True,
    )
    def test_service_name_from_env(self):
        # pylint: disable=protected-access
        cover = Coveralls()
        assert cover._coveralls_host == 'aaa'
        assert cover.config['parallel'] is True
        assert cover.config['repo_token'] == 'a1b2c3d4'
        assert cover.config['service_name'] == 'bbb'
        assert cover.config['flag_name'] == 'cc'
        assert cover.config['service_job_number'] == '1234'


@mock.patch.object(Coveralls, 'config_filename', '.coveralls.mock')
class CLIConfiguration(unittest.TestCase):
    def test_load_config(self):
        # pylint: disable=protected-access
        cover = Coveralls(
            repo_token='yyy',
            service_name='coveralls-aaa',
            coveralls_host='https://coveralls.aaa.com',
        )
        assert cover.config['repo_token'] == 'yyy'
        assert cover.config['service_name'] == 'coveralls-aaa'
        assert cover._coveralls_host == 'https://coveralls.aaa.com'
