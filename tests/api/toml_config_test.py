import logging
import os
import pathlib
import sys
import unittest.mock

import pytest
try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from coveralls.configuration import resolve

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


pytestmark = pytest.mark.usefixtures('isolate_cwd')


def _write_pyproject(tmp_path: pathlib.Path, body: str) -> None:
    (tmp_path / 'pyproject.toml').write_text(body, encoding='utf-8')


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_reads_toml_file(tmp_path: pathlib.Path) -> None:
    _write_pyproject(
        tmp_path,
        '[tool.coveralls]\n'
        'repo_token = "xxx"\n'
        'service_name = "jenkins"\n',
    )
    config = resolve({})
    assert config.repo_token == 'xxx'
    assert config.service_name == 'jenkins'


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_toml_support_does_not_require_pyyaml(
    tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture,
) -> None:
    # TOML parsing is always available (stdlib tomllib / tomli), so a
    # pyproject-configured project must work even without PyYAML installed and
    # must not emit the PyYAML warning when no .coveralls.yml exists.
    _write_pyproject(tmp_path, '[tool.coveralls]\nrepo_token = "xxx"\n')
    with caplog.at_level(logging.WARNING):
        config = resolve({})
    assert config.repo_token == 'xxx'
    assert not caplog.records


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_toml_native_booleans_are_preserved(tmp_path: pathlib.Path) -> None:
    _write_pyproject(
        tmp_path,
        '[tool.coveralls]\nrepo_token = "xxx"\nparallel = true\n',
    )
    config = resolve({})
    assert config.parallel is True


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_toml_unknown_key_warns(
    tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture,
) -> None:
    _write_pyproject(
        tmp_path,
        '[tool.coveralls]\nrepo_token = "xxx"\nbogus_key = "nope"\n',
    )
    with caplog.at_level(logging.WARNING):
        config = resolve({})
    assert config.repo_token == 'xxx'
    assert 'bogus_key' in caplog.text
    assert 'pyproject.toml' in caplog.text


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_toml_aliases_and_deprecated_keys(
    tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture,
) -> None:
    _write_pyproject(
        tmp_path,
        '[tool.coveralls]\n'
        'repo_token = "xxx"\n'
        'coveralls_host = "https://old.example.com"\n'
        'config_file = "custom.rc"\n',
    )
    with caplog.at_level(logging.WARNING):
        config = resolve({})
    assert config.host == 'https://old.example.com'
    assert config.rcfile == 'custom.rc'
    # config_file warns and names pyproject.toml; coveralls_host stays silent.
    assert 'config_file' in caplog.text
    assert 'deprecated' in caplog.text
    assert 'pyproject.toml' in caplog.text
    assert 'coveralls_host' not in caplog.text


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_missing_tool_coveralls_table_is_ignored(
    tmp_path: pathlib.Path,
) -> None:
    # A pyproject.toml without a [tool.coveralls] table (the common case for
    # any Python project) provides no settings and must not error.
    _write_pyproject(tmp_path, '[tool.other]\nkey = "value"\n')
    config = resolve({})
    assert config.service_name == 'coveralls-python'
    assert config.repo_token is None


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_empty_tool_coveralls_table_is_ignored(
    tmp_path: pathlib.Path,
) -> None:
    _write_pyproject(tmp_path, '[tool.coveralls]\n')
    config = resolve({})
    assert config.service_name == 'coveralls-python'
    assert config.repo_token is None


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_malformed_toml_raises(tmp_path: pathlib.Path) -> None:
    _write_pyproject(tmp_path, '[tool.coveralls]\nrepo_token = \n')
    with pytest.raises(tomllib.TOMLDecodeError):
        resolve({})


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_non_table_tool_coveralls_raises(tmp_path: pathlib.Path) -> None:
    _write_pyproject(tmp_path, '[tool]\ncoveralls = "nope"\n')
    with pytest.raises(TypeError, match='expected a table'):
        resolve({})


@pytest.mark.skipif(yaml is None, reason='requires PyYAML')
@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_yaml_wins_over_toml_and_warns(
    tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture,
) -> None:
    # First file with settings wins, no merging: the legacy .coveralls.yml
    # takes precedence over pyproject.toml and the collision is flagged.
    (tmp_path / '.coveralls.yml').write_text(
        'repo_token: from_yaml\n', encoding='utf-8',
    )
    _write_pyproject(
        tmp_path,
        '[tool.coveralls]\nrepo_token = "from_toml"\n',
    )
    with caplog.at_level(logging.WARNING):
        config = resolve({})

    assert config.repo_token == 'from_yaml'
    # The collision warning names both files and flags the YAML as legacy.
    assert '.coveralls.yml' in caplog.text
    assert 'pyproject.toml' in caplog.text
    assert 'legacy' in caplog.text


@pytest.mark.skipif(yaml is None, reason='requires PyYAML')
@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_empty_yaml_falls_through_to_toml(
    tmp_path: pathlib.Path, caplog: pytest.LogCaptureFixture,
) -> None:
    # An empty .coveralls.yml provides no settings, so pyproject.toml is used
    # and no collision warning is emitted.
    (tmp_path / '.coveralls.yml').write_text('\n', encoding='utf-8')
    _write_pyproject(
        tmp_path,
        '[tool.coveralls]\nrepo_token = "from_toml"\n',
    )
    with caplog.at_level(logging.WARNING):
        config = resolve({})

    assert config.repo_token == 'from_toml'
    assert not caplog.records
