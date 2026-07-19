import os
import unittest.mock

import pytest
try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from coveralls.configuration import Config
from coveralls.configuration import log
from coveralls.configuration import resolve


def resolve_config(**overrides):
    return resolve('.coveralls.mock', overrides)


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_no_environment_defaults():
    config = resolve_config()
    assert config.service_name == 'coveralls-python'
    assert config.repo_token is None
    assert config.token_required is True


@unittest.mock.patch.dict(
    os.environ,
    {'TRAVIS': 'True', 'TRAVIS_JOB_ID': '777'},
    clear=True,
)
def test_travis_waives_token_requirement():
    config = resolve_config()
    assert config.service_name == 'travis-ci'
    assert config.service_job_id == '777'
    assert config.token_required is False
    assert config.repo_token is None


@unittest.mock.patch.dict(
    os.environ,
    {
        'APPVEYOR': 'True',
        'APPVEYOR_BUILD_ID': '1234567',
        'APPVEYOR_PULL_REQUEST_NUMBER': '1234',
    },
    clear=True,
)
def test_appveyor():
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
def test_buildkite_no_pr():
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
def test_circleci_singular():
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
def test_circleci_parallel():
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
def test_github_repo_token_from_env():
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
def test_github_token_no_pr():
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
def test_jenkins():
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
def test_semaphore_classic():
    config = resolve_config(repo_token='xxx')
    assert config.service_name == 'semaphore-ci'
    assert config.service_job_id == 'a26d42cf'
    assert config.service_number == '36980c73'
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
def test_generic_ci():
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
def test_generic_ci_name_wins_over_specific_service():
    config = resolve_config(repo_token='xxx')
    assert config.service_name == 'generic-ci'
    # ...but the specific service still contributes its number
    assert config.service_number == '888'


@unittest.mock.patch.dict(
    os.environ,
    {
        'COVERALLS_HOST': 'https://enterprise.example.com',
        'COVERALLS_PARALLEL': 'true',
        'COVERALLS_REPO_TOKEN': 'a1b2c3d4',
        'COVERALLS_SERVICE_NAME': 'bbb',
        'COVERALLS_FLAG_NAME': 'cc',
        'COVERALLS_SERVICE_JOB_NUMBER': '1234',
        'COVERALLS_SKIP_SSL_VERIFY': '1',
        'COVERALLS_TIMEOUT': '30',
    },
    clear=True,
)
def test_environment_variables():
    config = resolve_config()
    assert config.host == 'https://enterprise.example.com'
    assert config.parallel is True
    assert config.repo_token == 'a1b2c3d4'
    assert config.service_name == 'bbb'
    assert config.flag_name == 'cc'
    assert config.service_job_number == '1234'
    assert config.skip_ssl_verify is True
    assert config.timeout == 30.0


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_overrides_win_over_environment():
    with unittest.mock.patch.dict(os.environ, {'COVERALLS_HOST': 'env'}):
        config = resolve_config(host='cli', service_name='cli-service')
    assert config.host == 'cli'
    assert config.service_name == 'cli-service'


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_none_overrides_do_not_clobber():
    env = {'COVERALLS_SERVICE_NAME': 'env'}
    with unittest.mock.patch.dict(os.environ, env):
        config = resolve_config(service_name=None)
    assert config.service_name == 'env'


@unittest.mock.patch.dict(
    os.environ, {'TRAVIS': 'True'}, clear=True,
)
def test_override_cannot_reimpose_waived_token():
    # debug/output pass token_required implicitly; travis waives it. Neither an
    # explicit True override nor travis should be able to flip it back on.
    config = resolve_config(token_required=True)
    assert config.token_required is False


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_override_waives_token():
    config = resolve_config(token_required=False)
    assert config.token_required is False


@pytest.mark.skipif(yaml is None, reason='requires PyYAML')
@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_file_source_and_unknown_key_warning(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / '.coveralls.mock').write_text(
        'repo_token: xxx\nservice_name: jenkins\nbogus_key: nope\n',
    )
    with unittest.mock.patch.object(log, 'warning') as warning:
        config = resolve('.coveralls.mock', {})

    assert config.repo_token == 'xxx'
    assert config.service_name == 'jenkins'
    warning.assert_called_once_with(
        'Ignoring unknown config option %r from %s.',
        'bogus_key', '.coveralls.mock',
    )


@pytest.mark.skipif(yaml is not None, reason='requires no PyYAML')
@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_file_source_without_yaml_warns():
    with unittest.mock.patch.object(log, 'warning') as warning:
        resolve('.coveralls.mock', {})
    warning.assert_called_once_with(
        'PyYAML is not installed, skipping %s.', '.coveralls.mock',
    )


def test_resolve_returns_config_instance():
    assert isinstance(resolve_config(), Config)


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_deprecated_override_keys_still_work():
    with unittest.mock.patch.object(log, 'warning') as warning:
        config = resolve_config(
            repo_token='x',
            coveralls_host='https://old.example.com',
            config_file='custom.rc',
        )
    assert config.host == 'https://old.example.com'
    assert config.rcfile == 'custom.rc'
    warning.assert_any_call(
        '%r is deprecated and will be removed in a future release; use %r '
        'instead (in %s).', 'coveralls_host', 'host', 'arguments',
    )
    warning.assert_any_call(
        '%r is deprecated and will be removed in a future release; use %r '
        'instead (in %s).', 'config_file', 'rcfile', 'arguments',
    )


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_deprecated_key_does_not_override_explicit_canonical():
    config = resolve_config(
        repo_token='x',
        host='https://new.example.com',
        coveralls_host='https://old.example.com',
    )
    assert config.host == 'https://new.example.com'


@pytest.mark.skipif(yaml is None, reason='requires PyYAML')
@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_none_rcfile_override_keeps_file_value(tmp_path, monkeypatch):
    # The CLI forwards rcfile=None when --rcfile is not passed; that must not
    # override an rcfile/config_file set in the config file.
    monkeypatch.chdir(tmp_path)
    (tmp_path / '.coveralls.mock').write_text(
        'repo_token: xxx\nconfig_file: from_yaml.rc\n',
    )
    config = resolve('.coveralls.mock', {'rcfile': None})
    assert config.rcfile == 'from_yaml.rc'


@pytest.mark.skipif(yaml is None, reason='requires PyYAML')
@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_deprecated_file_keys_still_work(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / '.coveralls.mock').write_text(
        'repo_token: xxx\n'
        'coveralls_host: https://old.example.com\n'
        'config_file: custom.rc\n',
    )
    with unittest.mock.patch.object(log, 'warning') as warning:
        config = resolve('.coveralls.mock', {})

    assert config.host == 'https://old.example.com'
    assert config.rcfile == 'custom.rc'
    warning.assert_any_call(
        '%r is deprecated and will be removed in a future release; use %r '
        'instead (in %s).', 'coveralls_host', 'host', '.coveralls.mock',
    )
