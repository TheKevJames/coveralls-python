import os
import pathlib
import subprocess
import sys
import unittest.mock

import pytest

from coveralls import Coveralls


COVERAGE_CODE_STANZA = """
import sys
sys.path.append('{}')

import inttest
inttest.test_func({:d})
"""

COVERAGE_TEMPLATE_PATH = pathlib.Path(__file__).parent / 'data'

GITINFO = {
    'GIT_ID': 'asdf1234',
    'GIT_AUTHOR_NAME': 'Integration Tests',
    'GIT_AUTHOR_EMAIL': 'integration@test.com',
    'GIT_COMMITTER_NAME': 'Integration Tests',
    'GIT_COMMITTER_EMAIL': 'integration@test.com',
    'GIT_MESSAGE': 'Ran the integration tests',
}


class TestIntegration:
    @staticmethod
    def _test_harness(
        tmp_path: pathlib.Path,
        monkeypatch: pytest.MonkeyPatch,
        num: int,
        hits: int,
    ) -> None:
        monkeypatch.chdir(tmp_path)

        test_file = tmp_path / 'test.py'
        test_file.write_text(
            COVERAGE_CODE_STANZA.format(COVERAGE_TEMPLATE_PATH, num),
            encoding='utf-8',
        )

        subprocess.check_call([
            sys.executable, '-m', 'coverage', 'run',
            str(test_file),
        ])

        coverallz = Coveralls(repo_token='xxx')
        report = coverallz.create_data()
        coverallz.create_report()  # This is purely for coverage

        source_files = {f['name'] for f in report['source_files']}
        print(source_files)
        inttest = str(COVERAGE_TEMPLATE_PATH / 'inttest.py')
        assert inttest in source_files

        lines: list[int | None] | None = next(
            (
                f['coverage'] for f in report['source_files']
                if f['name'] == inttest
            ), None,
        )
        assert lines is not None
        assert sum(int(bool(x)) for x in lines) == hits

    @unittest.mock.patch.dict(os.environ, GITINFO, clear=True)
    def test_5(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        self._test_harness(tmp_path, monkeypatch, 5, 8)

    @unittest.mock.patch.dict(os.environ, GITINFO, clear=True)
    def test_7(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        self._test_harness(tmp_path, monkeypatch, 7, 9)

    @unittest.mock.patch.dict(os.environ, GITINFO, clear=True)
    def test_11(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        self._test_harness(tmp_path, monkeypatch, 11, 9)
