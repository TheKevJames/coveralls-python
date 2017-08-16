# coding: utf-8
from __future__ import unicode_literals

import os
import unittest

import mock
import pytest

from coveralls import Coveralls


@mock.patch.object(Coveralls, 'config_filename', '.coveralls.mock')
class NoConfig(unittest.TestCase):
    @mock.patch.dict(os.environ, {'TRAVIS': 'True',
                                  'TRAVIS_JOB_ID': '777'}, clear=True)
    def test_travis_no_config(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'travis-ci'
        assert cover.config['service_job_id'] == '777'
        assert 'repo_token' not in cover.config

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
        with pytest.raises(Exception) as e:
            Coveralls()

        assert str(e.value) == ('Not on Travis or CircleCI. You have to '
                                'provide either repo_token in .coveralls.mock '
                                'or set the COVERALLS_REPO_TOKEN env var.')

    @mock.patch.dict(
        os.environ,
        {'CIRCLECI': 'True',
         'CIRCLE_BUILD_NUM': '888',
         'CI_PULL_REQUEST': 'https://github.com/org/repo/pull/9999'},
        clear=True)
    def test_circleci_no_config(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'circle-ci'
        assert cover.config['service_job_id'] == '888'
        assert cover.config['service_pull_request'] == '9999'

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
                                  'BUILDKITE_JOB_ID': '1234567'}, clear=True)
    def test_buildkite_no_config(self):
        cover = Coveralls(repo_token='xxx')
        assert cover.config['service_name'] == 'buildkite'
        assert cover.config['service_job_id'] == '1234567'
