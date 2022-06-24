import os
import re
import subprocess
import tempfile
import unittest
from unittest import mock

import coveralls.git
from coveralls.exception import CoverallsException

GIT_COMMIT_MSG = 'first commit'
GIT_EMAIL = 'me@here.com'
GIT_NAME = 'Daniël'
GIT_REMOTE = 'origin'
GIT_URL = 'https://github.com/username/Hello-World.git'


class GitTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_cwd = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.old_cwd)

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.chdir(self.dir)

        # TODO: switch to pathlib
        open('README', 'a').close()  # pylint: disable=consider-using-with

        subprocess.call(['git', 'init'], cwd=self.dir)
        subprocess.call(['git', 'config', 'user.name',
                         '"{}"'.format(GIT_NAME)], cwd=self.dir)
        subprocess.call(['git', 'config', 'user.email',
                         '"{}"'.format(GIT_EMAIL)], cwd=self.dir)
        subprocess.call(['git', 'add', 'README'], cwd=self.dir)
        subprocess.call(['git', 'commit', '-m', GIT_COMMIT_MSG], cwd=self.dir)
        subprocess.call(['git', 'remote', 'add', GIT_REMOTE, GIT_URL],
                        cwd=self.dir)

    @mock.patch.dict(os.environ, {'TRAVIS_BRANCH': 'master'}, clear=True)
    def test_git(self):
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
                'remotes': [{
                    'url': GIT_URL,
                    'name': GIT_REMOTE
                }],
                'branch': 'master'
            }
        }


class GitLogTest(GitTest):
    def test_gitlog(self):
        git_info = coveralls.git.gitlog('%H')
        assert re.match(r'^[a-f0-9]{40}$', git_info)

        assert coveralls.git.gitlog('%aN') == GIT_NAME
        assert coveralls.git.gitlog('%ae') == GIT_EMAIL
        assert coveralls.git.gitlog('%cN') == GIT_NAME
        assert coveralls.git.gitlog('%ce') == GIT_EMAIL
        assert coveralls.git.gitlog('%s') == GIT_COMMIT_MSG


class GitInfoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_cwd = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.old_cwd)

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        os.chdir(self.dir)

    @mock.patch.dict(os.environ, {
        'GIT_ID': '5e837ce92220be64821128a70f6093f836dd2c05',
        'GIT_BRANCH': 'master',
        'GIT_AUTHOR_NAME': GIT_NAME,
        'GIT_AUTHOR_EMAIL': GIT_EMAIL,
        'GIT_COMMITTER_NAME': GIT_NAME,
        'GIT_COMMITTER_EMAIL': GIT_EMAIL,
        'GIT_MESSAGE': GIT_COMMIT_MSG,
        'GIT_URL': GIT_URL,
        'GIT_REMOTE': GIT_REMOTE,
    }, clear=True)
    def test_gitinfo_envvars(self):
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
                'remotes': [{
                    'url': GIT_URL,
                    'name': GIT_REMOTE,
                }],
                'branch': 'master',
            },
        }

    def test_gitinfo_not_a_git_repo(self):
        git_info = coveralls.git.git_info()

        self.assertRaises(CoverallsException)
        assert not git_info


class GitInfoOverridesTest(unittest.TestCase):
    @mock.patch.dict(os.environ, {
        'GITHUB_ACTIONS': 'true',
        'GITHUB_REF': 'refs/pull/1234/merge',
        'GITHUB_SHA': 'bb0e00166b28f49db04d6a8b8cb4bddb5afa529f',
        'GITHUB_HEAD_REF': 'fixup-branch'
    }, clear=True)
    def test_gitinfo_github_pr(self):
        git_info = coveralls.git.git_info()
        assert git_info['git']['branch'] == 'fixup-branch'

    @mock.patch.dict(os.environ, {
        'GITHUB_ACTIONS': 'true',
        'GITHUB_REF': 'refs/heads/master',
        'GITHUB_SHA': 'bb0e00166b28f49db04d6a8b8cb4bddb5afa529f',
        'GITHUB_HEAD_REF': ''
    }, clear=True)
    def test_gitinfo_github_branch(self):
        git_info = coveralls.git.git_info()
        assert git_info['git']['branch'] == 'master'

    @mock.patch.dict(os.environ, {
        'GITHUB_ACTIONS': 'true',
        'GITHUB_REF': 'refs/tags/v1.0',
        'GITHUB_SHA': 'bb0e00166b28f49db04d6a8b8cb4bddb5afa529f',
        'GITHUB_HEAD_REF': ''
    }, clear=True)
    def test_gitinfo_github_tag(self):
        git_info = coveralls.git.git_info()
        assert git_info['git']['branch'] == 'v1.0'
