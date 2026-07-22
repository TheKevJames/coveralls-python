import pathlib

import pytest


@pytest.fixture(scope='function')
def isolate_cwd(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Run a test in a clean, empty working directory.

    Load-bearing for the config-resolution tests: resolve() and Coveralls()
    discover config files (.coveralls.yml, pyproject.toml) relative to the cwd,
    so without this a test would read coveralls-python's own pyproject.toml and
    resolve against it. It is deliberately not autouse -- other tests in this
    package (reporter/wear/encoding) chdir elsewhere on purpose -- so modules
    opt in with ``pytestmark = pytest.mark.usefixtures('isolate_cwd')``.
    """
    monkeypatch.chdir(tmp_path)
