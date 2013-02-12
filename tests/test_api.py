# coding: utf-8
import os
import re
import shutil
import tempfile
import unittest
import sh
from mock import patch
from sure import expect

from coveralls import Coveralls


class GitBasedTest(unittest.TestCase):

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        sh.cd(self.dir)
        sh.git.init()
        sh.git('config', 'user.name', '"Guido"')
        sh.git('config', 'user.email', '"me@here.com"')
        sh.touch('README')
        sh.git.add('README')
        sh.git.commit('-m', 'first commit')
        sh.git('remote', 'add', 'origin', 'https://github.com/username/Hello-World.git')

    def tearDown(self):
        shutil.rmtree(self.dir)


@patch.object(Coveralls, 'config_filename', '.coveralls.mock')
class Configration(unittest.TestCase):

    def setUp(self):
        with open('.coveralls.mock', 'w+') as fp:
            fp.write('repo_token: xxx\n')
            fp.write('service_name: jenkins\n')

    def tearDown(self):
        os.remove('.coveralls.mock')

    @patch.dict(os.environ, {}, clear=True)
    def test_local_with_config(self):
        cover = Coveralls()
        expect(cover.config['service_name']).to.equal('jenkins')
        expect(cover.config['repo_token']).to.equal('xxx')
        expect(cover.config).should_not.have.key('service_job_id')


@patch.object(Coveralls, 'config_filename', '.coveralls.mock')
class NoConfig(unittest.TestCase):

    @patch.dict(os.environ, {'TRAVIS': 'True', 'TRAVIS_JOB_ID': '777'})
    def test_travis_no_config(self):
        cover = Coveralls()
        expect(cover.config['service_name']).to.equal('travis-ci')
        expect(cover.config['service_job_id']).to.equal('777')
        expect(cover.config).should_not.have.key('repo_token')


class Git(GitBasedTest):

    def test_git(self):
        cover = Coveralls(repo_token='xxx')
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


class ReporterTest(unittest.TestCase):

    def test_reporter(self):
        os.chdir('/Users/prophet/projects/coveralls-python/example')
        sh.coverage('run', 'runtests.py')
        cover = Coveralls(repo_token='xxx')
        expect(cover.get_coverage()).should.be.equal([{'source': '# coding: utf-8\n\n\ndef hello():\n    print \'world\'\n\n\nclass Foo(object):\n    """ Bar """\n\n\ndef baz():\n    print \'this is not tested\'', 'name': 'project.py', 'coverage': [None, None, None, 1, 0, None, None, 1, None, None, None, 1, 0]}, {'source': '# coding: utf-8\nfrom project import hello\n\n\ndef test_hello():\n    hello()', 'name': 'runtests.py', 'coverage': [None, 1, None, None, 1, 0]}])