# coding: utf-8
from __future__ import unicode_literals

import os
import re
import shutil
import tempfile
import unittest

import mock
import sh

from coveralls import Coveralls


COMMIT_MSG = 'first commit'
EMAIL = 'me@here.com'
REMOTE_NAME = 'origin'
REMOTE_URL = 'https://github.com/user/repo.git'
USERNAME = 'Daniël'


class GitTest(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()

        sh.cd(self.dir)
        sh.touch('README')

        sh.git.init()
        sh.git.config('user.name', '"{}"'.format(USERNAME))
        sh.git.config('user.email', '"{}"'.format(EMAIL))
        sh.git.add('README')
        sh.git.commit('-m', COMMIT_MSG)
        sh.git.remote('add', REMOTE_NAME, REMOTE_URL)

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
                    'committer_email': EMAIL,
                    'author_email': EMAIL,
                    'author_name': USERNAME,
                    'message': COMMIT_MSG,
                    'committer_name': USERNAME,
                },
                'remotes': [{
                    'url': REMOTE_URL,
                    'name': REMOTE_NAME,
                }],
                'branch': 'master',
            }
        }
