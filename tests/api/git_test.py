# coding: utf-8
import os
import re
import shutil
import tempfile
import unittest

import mock
import sh

from coveralls import Coveralls


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
        cover = Coveralls(repo_token='xxx')
        git_info = cover.git_info()
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
