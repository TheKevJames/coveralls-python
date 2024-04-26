import os

import pytest


@pytest.fixture(scope='session', autouse=True)
def nuke_coverage():
    for folder in ('.', './example', './nonunicode'):
        try:
            os.remove(f'{folder}/.coverage')
        except FileNotFoundError:
            pass
