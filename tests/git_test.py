import os
import pathlib
import re
import subprocess
import unittest.mock

import pytest

import coveralls.git
from coveralls.git import run_command

GIT_COMMIT_MSG = 'first commit'
GIT_EMAIL = 'me@here.com'
GIT_NAME = 'Daniël'
GIT_REMOTE = 'origin'
GIT_URL = 'https://github.com/username/Hello-World.git'


def in_git_dir() -> bool:
    try:
        run_command('git', 'rev-parse')
    except Exception:
        return False

    return True


@pytest.fixture(scope='function')
def git_repo(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> pathlib.Path:
    monkeypatch.chdir(tmp_path)

    (tmp_path / 'README').touch()

    subprocess.call(['git', 'init'], cwd=tmp_path)
    subprocess.call(
        ['git', 'config', 'user.name', f'"{GIT_NAME}"'], cwd=tmp_path
    )
    subprocess.call(
        ['git', 'config', 'user.email', f'"{GIT_EMAIL}"'], cwd=tmp_path
    )
    subprocess.call(['git', 'add', 'README'], cwd=tmp_path)
    subprocess.call(['git', 'commit', '-m', GIT_COMMIT_MSG], cwd=tmp_path)
    subprocess.call(
        ['git', 'remote', 'add', GIT_REMOTE, GIT_URL], cwd=tmp_path
    )
    return tmp_path


@pytest.mark.usefixtures('git_repo')
class TestGit:
    @unittest.mock.patch.dict(
        os.environ, {'TRAVIS_BRANCH': 'master'}, clear=True
    )
    def test_git(self) -> None:
        git_info = coveralls.git.git_info()
        commit_id = git_info['git']['head'].pop('id')

        assert re.match(r'^[a-f0-9]{40}$', commit_id)
        assert git_info == {
            'git': {
                'head': {
                    'committer_email': GIT_EMAIL,
                    'author_email': GIT_EMAIL,
                    'author_name': GIT_NAME,
                    'message': GIT_COMMIT_MSG,
                    'committer_name': GIT_NAME,
                },
                'remotes': [{'url': GIT_URL, 'name': GIT_REMOTE}],
                'branch': 'master',
            }
        }


@pytest.mark.usefixtures('git_repo')
class TestGitLog:
    @pytest.mark.skipif(not in_git_dir(), reason='requires .git directory')
    def test_gitlog(self) -> None:
        git_info = coveralls.git.gitlog('%H')
        assert re.match(r'^[a-f0-9]{40}$', git_info)

        assert coveralls.git.gitlog('%aN') == GIT_NAME
        assert coveralls.git.gitlog('%ae') == GIT_EMAIL
        assert coveralls.git.gitlog('%cN') == GIT_NAME
        assert coveralls.git.gitlog('%ce') == GIT_EMAIL
        assert coveralls.git.gitlog('%s') == GIT_COMMIT_MSG


class TestGitInfo:
    @pytest.fixture(scope='function', autouse=True)
    def _chdir_tmp(
        self, tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.chdir(tmp_path)

    @unittest.mock.patch.dict(
        os.environ,
        {
            'GIT_ID': '5e837ce92220be64821128a70f6093f836dd2c05',
            'GIT_BRANCH': 'master',
            'GIT_AUTHOR_NAME': GIT_NAME,
            'GIT_AUTHOR_EMAIL': GIT_EMAIL,
            'GIT_COMMITTER_NAME': GIT_NAME,
            'GIT_COMMITTER_EMAIL': GIT_EMAIL,
            'GIT_MESSAGE': GIT_COMMIT_MSG,
            'GIT_URL': GIT_URL,
            'GIT_REMOTE': GIT_REMOTE,
        },
        clear=True,
    )
    def test_gitinfo_envvars(self) -> None:
        git_info = coveralls.git.git_info()
        commit_id = git_info['git']['head'].pop('id')
        assert re.match(r'^[a-f0-9]{40}$', commit_id)

        assert git_info == {
            'git': {
                'head': {
                    'committer_email': GIT_EMAIL,
                    'author_email': GIT_EMAIL,
                    'author_name': GIT_NAME,
                    'message': GIT_COMMIT_MSG,
                    'committer_name': GIT_NAME,
                },
                'remotes': [{'url': GIT_URL, 'name': GIT_REMOTE}],
                'branch': 'master',
            }
        }

    def test_gitinfo_not_a_git_repo(self) -> None:
        git_info = coveralls.git.git_info()

        assert not git_info


class TestGitInfoOverrides:
    @pytest.mark.skipif(not in_git_dir(), reason='requires .git directory')
    @unittest.mock.patch.dict(
        os.environ,
        {
            'GITHUB_ACTIONS': 'true',
            'GITHUB_REF': 'refs/pull/1234/merge',
            'GITHUB_SHA': 'bb0e00166b28f49db04d6a8b8cb4bddb5afa529f',
            'GITHUB_HEAD_REF': 'fixup-branch',
        },
        clear=True,
    )
    def test_gitinfo_github_pr(self) -> None:
        git_info = coveralls.git.git_info()
        assert git_info['git']['branch'] == 'fixup-branch'

    @pytest.mark.skipif(not in_git_dir(), reason='requires .git directory')
    @unittest.mock.patch.dict(
        os.environ,
        {
            'GITHUB_ACTIONS': 'true',
            'GITHUB_REF': 'refs/heads/master',
            'GITHUB_SHA': 'bb0e00166b28f49db04d6a8b8cb4bddb5afa529f',
            'GITHUB_HEAD_REF': '',
        },
        clear=True,
    )
    def test_gitinfo_github_branch(self) -> None:
        git_info = coveralls.git.git_info()
        assert git_info['git']['branch'] == 'master'

    @pytest.mark.skipif(not in_git_dir(), reason='requires .git directory')
    @unittest.mock.patch.dict(
        os.environ,
        {
            'GITHUB_ACTIONS': 'true',
            'GITHUB_REF': 'refs/tags/v1.0',
            'GITHUB_SHA': 'bb0e00166b28f49db04d6a8b8cb4bddb5afa529f',
            'GITHUB_HEAD_REF': '',
        },
        clear=True,
    )
    def test_gitinfo_github_tag(self) -> None:
        git_info = coveralls.git.git_info()
        assert git_info['git']['branch'] == 'v1.0'
