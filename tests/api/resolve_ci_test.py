import os
import unittest.mock
from typing import Any

import pytest

from coveralls.configuration import Config
from coveralls.configuration import resolve


pytestmark = pytest.mark.usefixtures('isolate_cwd')


def resolve_config(
    *, token_required: bool = True, **overrides: Any,
) -> Config:
    return resolve(overrides, token_required=token_required)


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_no_environment_defaults() -> None:
    config = resolve_config()
    assert config.service_name == 'coveralls-python'
    assert config.repo_token is None
    assert config.token_required


@unittest.mock.patch.dict(
    os.environ,
    {'TRAVIS': 'True', 'TRAVIS_JOB_ID': '777'},
    clear=True,
)
def test_travis_waives_token_requirement() -> None:
    config = resolve_config()
    assert config.service_name == 'travis-ci'
    assert config.service_job_id == '777'
    assert not config.token_required
    assert config.repo_token is None


@unittest.mock.patch.dict(
    os.environ,
    {'TRAVIS': 'True', 'TRAVIS_JOB_ID': '777', 'TRAVIS_PULL_REQUEST': 'false'},
    clear=True,
)
def test_travis_no_pr_false_sentinel() -> None:
    # Travis sets TRAVIS_PULL_REQUEST='false' on non-PR builds; the shared
    # trailing-integer parser drops the sentinel like it does for Buildkite.
    config = resolve_config(repo_token='xxx')
    assert config.service_name == 'travis-ci'
    assert config.service_pull_request is None


@unittest.mock.patch.dict(
    os.environ,
    {
        'APPVEYOR': 'True',
        'APPVEYOR_BUILD_ID': '1234567',
        'APPVEYOR_PULL_REQUEST_NUMBER': '1234',
    },
    clear=True,
)
def test_appveyor() -> None:
    config = resolve_config(repo_token='xxx')
    assert config.service_name == 'appveyor'
    assert config.service_job_id == '1234567'
    assert config.service_pull_request == '1234'


@unittest.mock.patch.dict(
    os.environ,
    {
        'BUILDKITE': 'True',
        'BUILDKITE_JOB_ID': '1234567',
        'BUILDKITE_PULL_REQUEST': 'false',
    },
    clear=True,
)
def test_buildkite_no_pr() -> None:
    config = resolve_config(repo_token='xxx')
    assert config.service_name == 'buildkite'
    assert config.service_job_id == '1234567'
    assert config.service_pull_request is None


@unittest.mock.patch.dict(
    os.environ,
    {
        'CIRCLECI': 'True',
        'CIRCLE_BUILD_NUM': '888',
        'CI_PULL_REQUEST': 'https://github.com/org/repo/pull/9999',
    },
    clear=True,
)
def test_circleci_singular() -> None:
    config = resolve_config(repo_token='xxx')
    assert config.service_name == 'circleci'
    assert config.service_number == '888'
    assert config.service_pull_request == '9999'


@unittest.mock.patch.dict(
    os.environ,
    {
        'CIRCLECI': 'True',
        'CIRCLE_WORKFLOW_ID': '0ea2c0f7-4e56-4a94-bf77-bfae6bdbf80a',
        'CIRCLE_NODE_INDEX': '15',
    },
    clear=True,
)
def test_circleci_parallel() -> None:
    config = resolve_config(repo_token='xxx')
    assert config.service_name == 'circleci'
    assert config.service_number == '0ea2c0f7-4e56-4a94-bf77-bfae6bdbf80a'
    assert config.service_job_id == '15'


@unittest.mock.patch.dict(
    os.environ,
    {
        'GITHUB_ACTIONS': 'true',
        'GITHUB_REF': 'refs/pull/1234/merge',
        'GITHUB_RUN_ID': '123456789',
        'COVERALLS_REPO_TOKEN': 'xxx',
    },
    clear=True,
)
def test_github_repo_token_from_env() -> None:
    config = resolve_config()
    assert config.service_name == 'github'
    assert config.service_pull_request == '1234'
    assert config.service_number == '123456789'
    assert config.service_job_id == '123456789'
    assert config.repo_token == 'xxx'


@unittest.mock.patch.dict(
    os.environ,
    {
        'GITHUB_ACTIONS': 'true',
        'GITHUB_TOKEN': 'ght',
        'GITHUB_REF': 'refs/heads/master',
        'GITHUB_RUN_ID': '987654321',
    },
    clear=True,
)
def test_github_token_no_pr() -> None:
    config = resolve_config()
    assert config.service_name == 'github'
    assert config.repo_token == 'ght'
    assert config.service_pull_request is None


@unittest.mock.patch.dict(
    os.environ,
    {
        'JENKINS_HOME': '/var/lib/jenkins',
        'BUILD_NUMBER': '888',
        'CI_PULL_REQUEST': 'https://github.com/org/repo/pull/9999',
    },
    clear=True,
)
def test_jenkins() -> None:
    config = resolve_config(repo_token='xxx')
    assert config.service_name == 'jenkins'
    assert config.service_job_id == '888'
    assert config.service_pull_request == '9999'


@unittest.mock.patch.dict(
    os.environ,
    {
        'SEMAPHORE': 'True',
        'SEMAPHORE_EXECUTABLE_UUID': '36980c73',
        'SEMAPHORE_JOB_UUID': 'a26d42cf',
        'SEMAPHORE_BRANCH_ID': '9999',
    },
    clear=True,
)
def test_semaphore_classic() -> None:
    config = resolve_config(repo_token='xxx')
    assert config.service_name == 'semaphore-ci'
    assert config.service_job_id == 'a26d42cf'
    assert config.service_number == '36980c73'
    assert config.service_pull_request == '9999'


@unittest.mock.patch.dict(
    os.environ,
    {
        'SEMAPHORE': 'True',
        'SEMAPHORE_WORKFLOW_ID': 'b86b3adf',
        'SEMAPHORE_JOB_ID': '2b942b49',
        'SEMAPHORE_GIT_PR_NUMBER': '9999',
    },
    clear=True,
)
def test_semaphore_20() -> None:
    config = resolve_config(repo_token='xxx')
    assert config.service_name == 'semaphore-ci'
    assert config.service_job_id == '2b942b49'
    assert config.service_number == 'b86b3adf'
    assert config.service_pull_request == '9999'


@unittest.mock.patch.dict(
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
def test_generic_ci() -> None:
    config = resolve_config()
    assert config.service_name == 'generic-ci'
    assert config.service_job_id == 'bb0e00166'
    assert config.service_branch == 'fixup-branch'
    assert config.service_pull_request == '1234'


@unittest.mock.patch.dict(
    os.environ,
    {'CIRCLECI': 'True', 'CI_NAME': 'generic-ci', 'CIRCLE_BUILD_NUM': '888'},
    clear=True,
)
def test_generic_ci_name_wins_over_specific_service() -> None:
    config = resolve_config(repo_token='xxx')
    assert config.service_name == 'generic-ci'
    # ...but the specific service still contributes its number
    assert config.service_number == '888'
