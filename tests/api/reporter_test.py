import contextlib
import os
import pathlib
import subprocess
import textwrap
import unittest.mock
from typing import Any

import pytest
import responses

from coveralls import Coveralls


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
EXAMPLE_DIR = os.path.join(BASE_DIR, 'example')


def assert_coverage(
    actual: dict[str, Any], expected: dict[str, Any],
) -> None:
    assert actual['source'].strip() == expected['source'].strip()
    assert actual['name'] == expected['name']
    assert actual['coverage'] == expected['coverage']
    assert actual.get('branches') == expected.get('branches')


class TestReporter:
    @pytest.fixture(scope='function', autouse=True)
    def _chdir_example(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(EXAMPLE_DIR)

        with contextlib.suppress(Exception):
            pathlib.Path('.coverage').unlink()

        with contextlib.suppress(Exception):
            pathlib.Path('extra.py').unlink()

    @staticmethod
    def make_test_results(
        with_branches: bool = False, name_prefix: str = '',
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        results = (
            {
                'source': (
                    pathlib.Path(EXAMPLE_DIR) / 'project.py'
                ).read_text(encoding='utf-8'),
                'name': f'{name_prefix}project.py',
                'coverage': [
                    1, 1, None, None, 1, None, None,
                    None, 1, 0, None, 1, 1, 1, 1, 1,
                ],
            }, {
                'source': textwrap.dedent("""
                from project import branch  # type: ignore[import-not-found]
                from project import hello

                if __name__ == '__main__':
                    hello()
                    branch(False, True)
                    branch(True, True)
                """),
                'name': f'{name_prefix}runtests.py',
                'coverage': [1, 1, None, 1, 1, 1, 1],
            },
        )
        if with_branches:
            results[0]['branches'] = [
                13, 0, 14, 1, 13, 0, 15, 1, 15, 0, 16, 1,
                15, 0, 12, 0,
            ]
            results[1]['branches'] = [4, 0, 5, 1, 4, 0, 1, 0]
        return results

    def test_reporter(self) -> None:
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'runtests.py',
            ], cwd=EXAMPLE_DIR,
        )
        results = Coveralls(repo_token='xxx').get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results()
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_no_base_dir_arg(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'example/runtests.py',
            ], cwd=BASE_DIR,
        )

        # without base_dir arg, file name is prefixed with 'example/'
        monkeypatch.chdir(BASE_DIR)
        results = Coveralls(repo_token='xxx').get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results(name_prefix='example/')
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_with_base_dir_arg(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'example/runtests.py',
            ], cwd=BASE_DIR,
        )

        # without base_dir arg, file name is prefixed with 'example/'
        monkeypatch.chdir(BASE_DIR)
        results = Coveralls(
            repo_token='xxx',
            base_dir='example',
        ).get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results()
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_with_base_dir_trailing_sep(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'example/runtests.py',
            ], cwd=BASE_DIR,
        )

        # without base_dir arg, file name is prefixed with 'example/'
        monkeypatch.chdir(BASE_DIR)
        results = Coveralls(
            repo_token='xxx',
            base_dir='example/',
        ).get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results()
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_with_src_dir_arg(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'example/runtests.py',
            ], cwd=BASE_DIR,
        )

        # without base_dir arg, file name is prefixed with 'example/'
        monkeypatch.chdir(BASE_DIR)
        results = Coveralls(
            repo_token='xxx',
            src_dir='src',
        ).get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results(name_prefix='src/example/')
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_with_src_dir_trailing_sep(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'example/runtests.py',
            ], cwd=BASE_DIR,
        )

        # without base_dir arg, file name is prefixed with 'example/'
        monkeypatch.chdir(BASE_DIR)
        results = Coveralls(
            repo_token='xxx',
            src_dir='src/',
        ).get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results(name_prefix='src/example/')
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_with_both_base_dir_and_src_dir_args(
        self, monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'example/runtests.py',
            ], cwd=BASE_DIR,
        )

        # without base_dir arg, file name is prefixed with 'example/'
        monkeypatch.chdir(BASE_DIR)
        results = Coveralls(
            repo_token='xxx',
            base_dir='example',
            src_dir='src',
        ).get_coverage()
        assert len(results) == 2

        expected_results = self.make_test_results(name_prefix='src/')
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_reporter_with_branches(self) -> None:
        subprocess.call(
            [
                'coverage', 'run', '--branch', '--omit=**/.tox/*',
                'runtests.py',
            ], cwd=EXAMPLE_DIR,
        )
        results = Coveralls(repo_token='xxx').get_coverage()
        assert len(results) == 2

        # Branches are expressed as four values each in a flat list
        assert not len(results[0]['branches']) % 4
        assert not len(results[1]['branches']) % 4

        expected_results = self.make_test_results(with_branches=True)
        assert_coverage(results[0], expected_results[0])
        assert_coverage(results[1], expected_results[1])

    def test_missing_file(self) -> None:
        pathlib.Path('extra.py').write_text(
            'print("Python rocks!")\n', encoding='utf-8',
        )
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'extra.py',
            ], cwd=EXAMPLE_DIR,
        )
        with contextlib.suppress(Exception):
            pathlib.Path('extra.py').unlink()

        with pytest.raises(RuntimeError, match='No source for code'):
            Coveralls(repo_token='xxx').get_coverage()

    def test_not_python(self) -> None:
        pathlib.Path('extra.py').write_text(
            'print("Python rocks!")\n', encoding='utf-8',
        )
        subprocess.call(
            [
                'coverage', 'run', '--omit=**/.tox/*',
                'extra.py',
            ], cwd=EXAMPLE_DIR,
        )
        pathlib.Path('extra.py').write_text(
            "<h1>This isn't python!</h1>\n", encoding='utf-8',
        )

        with pytest.raises(
                RuntimeError,
                match=r"Couldn't parse .* as Python",
        ):
            Coveralls(repo_token='xxx').get_coverage()

    @responses.activate
    def test_submit_report_422_github(self) -> None:
        responses.add(
            responses.POST, 'https://coveralls.io/api/v1/jobs',
            json={'error': 'nope'}, status=422,
        )
        cov = Coveralls(repo_token='test_token', service_name='github')

        with unittest.mock.patch('coveralls.api.log.warning') as mock_warn:
            with pytest.raises(RuntimeError):
                cov.submit_report('{}')
            mock_warn.assert_called()
            assert '422' in mock_warn.call_args_list[0][0][0]
