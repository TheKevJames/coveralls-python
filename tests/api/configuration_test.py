import os
import unittest.mock

import pytest
try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

from coveralls import Coveralls


# The per-source resolution rules (CI detection, env vars, file loading,
# precedence) are covered in resolve_test.py and config_test.py. These tests
# assert the Coveralls entrypoint consumes a resolved, typed Config correctly.
@unittest.mock.patch.object(Coveralls, 'config_filename', '.coveralls.mock')
class TestConfigIntegration:
    @pytest.mark.skipif(yaml is None, reason='requires PyYAML')
    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_reads_config_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / '.coveralls.mock').write_text(
            'repo_token: xxx\nservice_name: jenkins\n',
            encoding='utf-8',
        )

        cover = Coveralls()

        assert cover.config.service_name == 'jenkins'
        assert cover.config.repo_token == 'xxx'
        assert cover.config.service_job_id is None

    @unittest.mock.patch.dict(
        os.environ,
        {
            'COVERALLS_HOST': 'https://enterprise.example.com',
            'COVERALLS_PARALLEL': 'true',
            'COVERALLS_REPO_TOKEN': 'a1b2c3d4',
            'COVERALLS_SERVICE_NAME': 'bbb',
        },
        clear=True,
    )
    def test_reads_environment(self):
        cover = Coveralls()

        assert cover.config.host == 'https://enterprise.example.com'
        assert cover.config.parallel is True
        assert cover.config.repo_token == 'a1b2c3d4'
        assert cover.config.service_name == 'bbb'

    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_overrides_win(self):
        cover = Coveralls(
            repo_token='yyy',
            service_name='coveralls-aaa',
            host='https://coveralls.aaa.com',
        )

        assert cover.config.repo_token == 'yyy'
        assert cover.config.service_name == 'coveralls-aaa'
        assert cover.config.host == 'https://coveralls.aaa.com'

    @unittest.mock.patch.dict(
        os.environ,
        {'COVERALLS_REPO_TOKEN': 'xxx', 'COVERALLS_TIMEOUT': 'abc'},
        clear=True,
    )
    def test_invalid_timeout_raises_on_construction(self):
        with pytest.raises(ValueError, match='must be a number'):
            Coveralls()


@unittest.mock.patch.object(Coveralls, 'config_filename', '.coveralls.mock')
class TestEnsureToken:
    @unittest.mock.patch.dict(
        os.environ,
        {
            'TRAVIS': 'True',
            'TRAVIS_JOB_ID': '777',
            'COVERALLS_REPO_TOKEN': 'yyy',
        },
        clear=True,
    )
    def test_repo_token_from_env(self):
        cover = Coveralls()
        assert cover.config.service_name == 'travis-ci'
        assert cover.config.service_job_id == '777'
        assert cover.config.repo_token == 'yyy'

    @unittest.mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
    def test_travis_needs_no_token(self):
        cover = Coveralls()
        assert cover.config.token_required is False
        assert cover.config.repo_token is None

    @unittest.mock.patch.dict(os.environ, {}, clear=True)
    def test_misconfigured(self):
        with pytest.raises(RuntimeError) as excinfo:
            Coveralls()

        assert str(excinfo.value) == (
            'No supported CI found and no repo token configured. You have to '
            'provide either repo_token in .coveralls.mock or set the '
            'COVERALLS_REPO_TOKEN env var.'
        )

    @unittest.mock.patch.dict(
        os.environ,
        {'GITHUB_ACTIONS': 'true'},
        clear=True,
    )
    def test_misconfigured_github(self):
        with pytest.raises(RuntimeError) as excinfo:
            Coveralls()

        assert str(excinfo.value).startswith(
            'Running on Github Actions but GITHUB_TOKEN is not set.',
        )
