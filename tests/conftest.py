import contextlib
import pathlib

import pytest


@pytest.fixture(scope='session', autouse=True)
def nuke_coverage():
    for folder in ('.', './example', './nonunicode'):
        with contextlib.suppress(FileNotFoundError):
            pathlib.Path(f'{folder}/.coverage').unlink()
