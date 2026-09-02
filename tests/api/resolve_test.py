import logging
import os
import pathlib
import unittest.mock
from typing import Any

import pytest

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from coveralls.configuration import Config
from coveralls.configuration import resolve

pytestmark = pytest.mark.usefixtures('isolate_cwd')


def resolve_config(*, token_required: bool = True, **overrides: Any) -> Config:
    return resolve(overrides, token_required=token_required)


@unittest.mock.patch.dict(
    os.environ,
    {
        'COVERALLS_HOST': 'https://enterprise.example.com',
        'COVERALLS_PARALLEL': 'true',
        'COVERALLS_REPO_TOKEN': 'a1b2c3d4',
        'COVERALLS_SERVICE_NAME': 'bbb',
        'COVERALLS_FLAG_NAME': 'cc',
        'COVERALLS_CARRYFORWARD': 'flag1,flag2',
        'COVERALLS_SERVICE_JOB_NUMBER': '1234',
        'COVERALLS_SKIP_SSL_VERIFY': '1',
        'COVERALLS_TIMEOUT': '30',
        'COVERALLS_RETRIES': '4',
        'COVERALLS_RCFILE': 'custom.rc',
        'COVERALLS_BASE_DIR': 'base',
        'COVERALLS_SRC_DIR': 'src',
    },
    clear=True,
)
def test_environment_variables() -> None:
    config = resolve_config()
    assert config.host == 'https://enterprise.example.com'
    assert config.parallel is True
    assert config.repo_token == 'a1b2c3d4'
    assert config.service_name == 'bbb'
    assert config.flag_name == 'cc'
    assert config.carryforward == 'flag1,flag2'
    assert config.service_job_number == '1234'
    assert config.skip_ssl_verify
    assert config.timeout == 30.0
    assert config.retries == 4
    # base_dir/src_dir/rcfile complete the convention on the env interface
    assert config.rcfile == 'custom.rc'
    assert config.base_dir == 'base'
    assert config.src_dir == 'src'


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_overrides_win_over_environment() -> None:
    with unittest.mock.patch.dict(os.environ, {'COVERALLS_HOST': 'env'}):
        config = resolve_config(host='cli', service_name='cli-service')
    assert config.host == 'cli'
    assert config.service_name == 'cli-service'


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_none_overrides_do_not_clobber() -> None:
    env = {'COVERALLS_SERVICE_NAME': 'env'}
    with unittest.mock.patch.dict(os.environ, env):
        config = resolve_config(service_name=None)
    assert config.service_name == 'env'


@unittest.mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_override_cannot_reimpose_waived_token() -> None:
    # debug/output pass token_required implicitly; travis waives it. Neither an
    # explicit True override nor travis should be able to flip it back on.
    config = resolve_config(token_required=True)
    assert not config.token_required


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_override_waives_token() -> None:
    config = resolve_config(token_required=False)
    assert not config.token_required


@pytest.mark.skipif(yaml is None, reason='requires PyYAML')
@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_config_file_cannot_waive_token_required(
    tmp_path: pathlib.Path,
) -> None:
    # token_required is a security guard, not a user-facing setting: a
    # token_required: false in the config file must be ignored so a committed
    # .coveralls.yml cannot silently disable the check.
    (tmp_path / '.coveralls.yml').write_text(
        'token_required: false\n', encoding='utf-8'
    )
    config = resolve({})
    assert config.token_required


def test_bool_override_precedence_is_owned_by_resolve() -> None:
    # A None override means "unset" and must not clobber env/file; an explicit
    # False override wins. This is the single rule resolve() enforces for both
    # CLI (--no-parallel) and library callers.
    env = {'COVERALLS_PARALLEL': 'true', 'COVERALLS_SKIP_SSL_VERIFY': '1'}
    with unittest.mock.patch.dict(os.environ, env, clear=True):
        assert resolve_config(parallel=None).parallel is True
        assert resolve_config(parallel=False).parallel is False
        assert resolve_config(skip_ssl_verify=None).skip_ssl_verify
        assert not resolve_config(skip_ssl_verify=False).skip_ssl_verify


@pytest.mark.skipif(yaml is None, reason='requires PyYAML')
@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_file_source_and_unknown_key_warning(
    tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture
) -> None:
    (tmp_path / '.coveralls.yml').write_text(
        'repo_token: xxx\nservice_name: jenkins\n'
        'carryforward: flag1,flag2\nbogus_key: nope\n',
        encoding='utf-8',
    )
    with caplog.at_level(logging.WARNING):
        config = resolve({})

    assert config.repo_token == 'xxx'
    assert config.service_name == 'jenkins'
    assert config.carryforward == 'flag1,flag2'
    # Assert on the rendered warning, not the lazy-logging format + args: the
    # dropped key and its source file are the observable behaviour.
    assert 'bogus_key' in caplog.text
    assert '.coveralls.yml' in caplog.text


@pytest.mark.skipif(yaml is None, reason='requires PyYAML')
@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_bool_flags_are_coerced_from_config_file(
    tmp_path: pathlib.Path,
) -> None:
    # A config file may carry a non-bool (e.g. a quoted parallel: "yes"); it
    # must be normalized rather than forwarded to the API as a stray string.
    (tmp_path / '.coveralls.yml').write_text(
        'repo_token: xxx\nparallel: "yes"\nskip_ssl_verify: "1"\n',
        encoding='utf-8',
    )
    config = resolve({})
    assert config.parallel is True
    assert config.skip_ssl_verify


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_unknown_override_key_warns_and_is_dropped(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # Same rule as the config file: an unknown key from any source is dropped
    # with a warning rather than crashing (previously a raw TypeError from
    # Config(**merged) for an unexpected Coveralls() kwarg).
    with caplog.at_level(logging.WARNING):
        config = resolve_config(repo_token='xxx', bogus_key='nope')

    assert config.repo_token == 'xxx'
    assert not hasattr(config, 'bogus_key')
    assert 'bogus_key' in caplog.text
    assert 'arguments' in caplog.text


@pytest.mark.skipif(yaml is not None, reason='requires no PyYAML')
@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_file_source_without_yaml_warns(
    tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture
) -> None:
    # The warning fires only when the YAML file actually exists: an absent file
    # is silent so a TOML-only or env-only user is never nagged about PyYAML.
    (tmp_path / '.coveralls.yml').write_text(
        'repo_token: xxx\n', encoding='utf-8'
    )
    with caplog.at_level(logging.WARNING):
        resolve({})
    assert 'PyYAML is not installed' in caplog.text
    assert '.coveralls.yml' in caplog.text


def test_resolve_returns_config_instance() -> None:
    assert isinstance(resolve_config(), Config)


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_coveralls_host_alias_is_permanent_and_silent(
    caplog: pytest.LogCaptureFixture,
) -> None:
    # coveralls_host and host are both long-term spellings; the alias maps to
    # host and must NOT emit a deprecation warning.
    with caplog.at_level(logging.WARNING):
        config = resolve_config(
            repo_token='x', coveralls_host='https://old.example.com'
        )
    assert config.host == 'https://old.example.com'
    assert not caplog.records


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_deprecated_config_file_key_warns(
    caplog: pytest.LogCaptureFixture,
) -> None:
    with caplog.at_level(logging.WARNING):
        config = resolve_config(repo_token='x', config_file='custom.rc')
    assert config.rcfile == 'custom.rc'
    assert 'config_file' in caplog.text
    assert 'deprecated' in caplog.text
    assert 'rcfile' in caplog.text


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_alias_does_not_override_explicit_canonical() -> None:
    config = resolve_config(
        repo_token='x',
        host='https://new.example.com',
        coveralls_host='https://old.example.com',
    )
    assert config.host == 'https://new.example.com'


@pytest.mark.skipif(yaml is None, reason='requires PyYAML')
@pytest.mark.parametrize('content', ['', '\n\n', '# only a comment\n'])
@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_empty_config_file_is_ignored(
    content: str, tmp_path: pathlib.Path
) -> None:
    # yaml.safe_load() returns None for empty/comment-only files; resolve must
    # treat that as no config rather than crashing on a None update.
    (tmp_path / '.coveralls.yml').write_text(content, encoding='utf-8')

    config = resolve({})

    assert config.service_name == 'coveralls-python'
    assert config.repo_token is None


@pytest.mark.skipif(yaml is None, reason='requires PyYAML')
@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_none_rcfile_override_keeps_file_value(tmp_path: pathlib.Path) -> None:
    # The CLI forwards rcfile=None when --rcfile is not passed; that must not
    # override an rcfile/config_file set in the config file.
    (tmp_path / '.coveralls.yml').write_text(
        'repo_token: xxx\nconfig_file: from_yaml.rc\n', encoding='utf-8'
    )
    config = resolve({'rcfile': None})
    assert config.rcfile == 'from_yaml.rc'


@pytest.mark.skipif(yaml is None, reason='requires PyYAML')
@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_alias_and_deprecated_file_keys_still_work(
    tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture
) -> None:
    (tmp_path / '.coveralls.yml').write_text(
        'repo_token: xxx\n'
        'coveralls_host: https://old.example.com\n'
        'config_file: custom.rc\n',
        encoding='utf-8',
    )
    with caplog.at_level(logging.WARNING):
        config = resolve({})

    assert config.host == 'https://old.example.com'
    assert config.rcfile == 'custom.rc'
    # config_file is deprecated (warns) and names its source file; the
    # permanent coveralls_host alias must stay silent.
    assert 'config_file' in caplog.text
    assert 'deprecated' in caplog.text
    assert '.coveralls.yml' in caplog.text
    assert 'coveralls_host' not in caplog.text
