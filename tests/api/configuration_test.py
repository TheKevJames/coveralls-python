# pylint: disable=no-self-use
import os
import shutil
import tempfile
import unittest

import mock
import pytest
try:
    import yaml
except ImportError:
    yaml = None

from coveralls import Coveralls
from coveralls.api import log


@mock.patch.object(Coveralls, 'config_filename', '.coveralls.mock')
class Configuration(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

        os.chdir(self.dir)
        with open('.coveralls.mock', 'w+') as fp:
            fp.write('repo_token: xxx\n')
            fp.write('service_name: jenkins\n')

    def tearDown(self):
        shutil.rmtree(self.dir)

    @pytest.mark.skipif(yaml is None, reason='requires PyYAML')
    @mock.patch.dict(os.environ, {}, clear=True)
    def test_local_with_config(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'jenkins'
        assert cover.config['repo_token'] == 'xxx'
        assert 'service_job_id' not in cover.config

    @pytest.mark.skipif(yaml is not None, reason='requires no PyYAML')
    @mock.patch.object(log, 'warning')
    @mock.patch.dict(os.environ, {'COVERALLS_REPO_TOKEN': 'xxx'}, clear=True)
    def test_local_with_config_without_yaml_module(self, mock_logger):
        """test local with config in yaml, but without yaml-installed"""
        cover = Coveralls()
        mock_logger.assert_called_once_with(
            'PyYAML is not installed, skipping %s.', cover.config_filename)


@mock.patch.object(Coveralls, 'config_filename', '.coveralls.mock')
class NoConfiguration(unittest.TestCase):
    @mock.patch.dict(os.environ, {'TRAVIS': 'True',
                                  'TRAVIS_JOB_ID': '777',
                                  'COVERALLS_REPO_TOKEN': 'yyy'}, clear=True)
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
            '.coveralls.mock or set the COVERALLS_REPO_TOKEN env var.')

    @mock.patch.dict(os.environ, {'GITHUB_ACTIONS': 'true'}, clear=True)
    def test_misconfigured_github(self):
        with pytest.raises(Exception) as excinfo:
            Coveralls()

        assert str(excinfo.value).startswith(
            'Running on Github Actions but GITHUB_TOKEN is not set.')

    @mock.patch.dict(os.environ, {'APPVEYOR': 'True',
                                  'APPVEYOR_BUILD_ID': '1234567',
                                  'APPVEYOR_PULL_REQUEST_NUMBER': '1234'},
                     clear=True)
    def test_appveyor_no_config(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'appveyor'
        assert cover.config['service_job_id'] == '1234567'
        assert cover.config['service_pull_request'] == '1234'

    @mock.patch.dict(os.environ, {'BUILDKITE': 'True',
                                  'BUILDKITE_JOB_ID': '1234567',
                                  'BUILDKITE_PULL_REQUEST': '1234'},
                     clear=True)
    def test_buildkite_no_config(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'buildkite'
        assert cover.config['service_job_id'] == '1234567'
        assert cover.config['service_pull_request'] == '1234'

    @mock.patch.dict(os.environ, {'BUILDKITE': 'True',
                                  'BUILDKITE_JOB_ID': '1234567',
                                  'BUILDKITE_PULL_REQUEST': 'false'},
                     clear=True)
    def test_buildkite_no_config_no_pr(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'buildkite'
        assert cover.config['service_job_id'] == '1234567'
        assert 'service_pull_request' not in cover.config

    @mock.patch.dict(
        os.environ,
        {'CIRCLECI': 'True',
         'CIRCLE_BUILD_NUM': '888',
         'CI_PULL_REQUEST': 'https://github.com/org/repo/pull/9999'},
        clear=True)
    def test_circleci_no_config(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'circle-ci'
        assert cover.config['service_job_id'] == '888'
        assert cover.config['service_pull_request'] == '9999'

    @mock.patch.dict(
        os.environ,
        {'GITHUB_ACTIONS': 'true',
         'GITHUB_REF': 'refs/pull/1234/merge',
         'GITHUB_SHA': 'bb0e00166b28f49db04d6a8b8cb4bddb5afa529f',
         'GITHUB_RUN_ID': '123456789',
         'GITHUB_RUN_NUMBER': '12',
         'GITHUB_HEAD_REF': 'fixup-branch',
         'COVERALLS_REPO_TOKEN': 'xxx'},
        clear=True)
    def test_github_no_config(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'github-actions'
        assert cover.config['service_pull_request'] == '1234'
        assert cover.config['service_number'] == '123456789'
        assert 'service_job_id' not in cover.config

    @mock.patch.dict(
        os.environ,
        {'GITHUB_ACTIONS': 'true',
         'GITHUB_TOKEN': 'xxx',
         'GITHUB_REF': 'refs/heads/master',
         'GITHUB_SHA': 'bb0e00166b28f49db04d6a8b8cb4bddb5afa529f',
         'GITHUB_RUN_ID': '987654321',
         'GITHUB_RUN_NUMBER': '21',
         'GITHUB_HEAD_REF': ''},
        clear=True)
    def test_github_no_config_no_pr(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'github'
        assert cover.config['service_number'] == '987654321'
        assert 'service_job_id' not in cover.config
        assert 'service_pull_request' not in cover.config

    @mock.patch.dict(
        os.environ,
        {'JENKINS_HOME': '/var/lib/jenkins',
         'BUILD_NUMBER': '888',
         'CI_PULL_REQUEST': 'https://github.com/org/repo/pull/9999'},
        clear=True)
    def test_jenkins_no_config(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'jenkins'
        assert cover.config['service_job_id'] == '888'
        assert cover.config['service_pull_request'] == '9999'

    @mock.patch.dict(os.environ, {'TRAVIS': 'True',
                                  'TRAVIS_JOB_ID': '777'}, clear=True)
    def test_travis_no_config(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'travis-ci'
        assert cover.config['service_job_id'] == '777'
        assert 'repo_token' not in cover.config

    @mock.patch.dict(os.environ,
                     {'SEMAPHORE': 'True',
                      'SEMAPHORE_BUILD_NUMBER': '888',
                      'PULL_REQUEST_NUMBER': '9999'},
                     clear=True)
    def test_semaphore_no_config(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'semaphore-ci'
        assert cover.config['service_job_id'] == '888'
        assert cover.config['service_pull_request'] == '9999'

    @mock.patch.dict(os.environ, {'COVERALLS_SERVICE_NAME': 'xxx'}, clear=True)
    def test_service_name_from_env(self):
        cover = Coveralls(repo_token='yyy')
        assert cover.config['service_name'] == 'xxx'
