# coding: utf-8
import re
import shutil
import tempfile
import unittest
import sh
from sure import expect

from coveralls import Coveralls


class SimpleTest(unittest.TestCase):

    def test_git(self):
        cover = Coveralls(repo_token='xxx')
        dir = tempfile.mkdtemp()
        sh.cd(dir)
        sh.git.init()
        sh.git('config', 'user.name', '"Guido"')
        sh.git('config', 'user.email', '"me@here.com"')
        sh.touch('README')
        sh.git.add('README')
        sh.git.commit('-m', 'first commit')
        sh.git('remote', 'add', 'origin', 'https://github.com/username/Hello-World.git')

        git_info = cover.git_info()
        commit_id = git_info['git']['head'].pop('id')
        self.assertTrue(re.match(r'^[a-f0-9]{40}$', commit_id))
        # expect(commit_id).should.match(r'^[a-f0-9]{40}$', re.I | re.U) sure 1.1.7 is broken for py2.6

        expect(git_info).should.be.equal({'git': {
            'head': {
                'committer_email': 'me@here.com',
                'author_email': 'me@here.com',
                'author_name': 'Guido',
                'message': 'first commit',
                'committer_name': 'Guido',
            },
            'remotes': [{
                'url': u'https://github.com/username/Hello-World.git',
                'name': u'origin'
            }],
            'branch': u'master'}})

        shutil.rmtree(dir)