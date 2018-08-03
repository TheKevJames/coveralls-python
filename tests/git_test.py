# coding: utf-8
# pylint: disable=no-self-use
from __future__ import unicode_literals

import os
import re
import shutil
import tempfile
import unittest

import mock
import sh

import coveralls.git


GIT_COMMIT_MSG = 'first commit'
GIT_EMAIL = 'me@here.com'
GIT_NAME = 'Daniël'
GIT_REMOTE = 'origin'
GIT_URL = 'https://github.com/username/Hello-World.git'


class GitTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

        sh.cd(self.dir)
        sh.touch('README')

        sh.git.init()
        sh.git.config('user.name', '"{}"'.format(GIT_NAME))
        sh.git.config('user.email', '"{}"'.format(GIT_EMAIL))
        sh.git.add('README')
        sh.git.commit('-m', GIT_COMMIT_MSG)
        sh.git.remote('add', GIT_REMOTE, GIT_URL)

    def tearDown(self):
        shutil.rmtree(self.dir)

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
        gitlog = coveralls.git.gitlog
        
        git_info = gitlog('%H')
        assert re.match(r'^[a-f0-9]{40}$', git_info)

        assert gitlog('%aN') == GIT_NAME
        assert gitlog('%ae') == GIT_EMAIL
        assert gitlog('%cN') == GIT_NAME
        assert gitlog('%ce')== GIT_EMAIL
        assert gitlog('%s') == GIT_COMMIT_MSG


class GitInfoTestEnvVars(unittest.TestCase):

    @mock.patch.dict(os.environ, {
        'GIT_ID': '5e837ce92220be64821128a70f6093f836dd2c05',
        'GIT_BRANCH': 'master',
        'GIT_AUTHOR_NAME': GIT_NAME,
        'GIT_AUTHOR_EMAIL': GIT_EMAIL,
        'GIT_COMMITTER_NAME':GIT_NAME,
        'GIT_COMMITTER_EMAIL':GIT_EMAIL,
        'GIT_MESSAGE': GIT_COMMIT_MSG,
        'GIT_URL': GIT_URL,
        'GIT_REMOTE': GIT_REMOTE, 
    }, 
    clear=True)
    def test_gitlog_envvars(self):
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