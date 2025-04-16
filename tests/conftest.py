import contextlib
import os

import pytest


@pytest.fixture(scope='session', autouse=True)
def nuke_coverage():
    for folder in ('.', './example', './nonunicode'):
        with contextlib.suppress(FileNotFoundError):
            os.remove(f'{folder}/.coverage')
