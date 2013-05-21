# coding: utf-8
from __future__ import unicode_literals
import os
from os.path import join, dirname
import re
import shutil
import tempfile
import unittest
import coverage

import sh
from mock import patch
import pytest

from coveralls import Coveralls
from coveralls.api import log


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
        assert cover.config['service_name'] == 'jenkins'
        assert cover.config['repo_token'] == 'xxx'
        assert 'service_job_id' not in cover.config


@patch.object(Coveralls, 'config_filename', '.coveralls.mock')
class NoConfig(unittest.TestCase):

    @patch.dict(os.environ, {'TRAVIS': 'True', 'TRAVIS_JOB_ID': '777'}, clear=True)
    def test_travis_no_config(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'travis-ci'
        assert cover.config['service_job_id'] == '777'
        assert 'repo_token' not in cover.config

    @patch.dict(os.environ, {'TRAVIS': 'True', 'TRAVIS_JOB_ID': '777', 'COVERALLS_REPO_TOKEN': 'yyy'}, clear=True)
    def test_repo_token_from_env(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'travis-ci'
        assert cover.config['service_job_id'] == '777'
        assert cover.config['repo_token'] == 'yyy'

    @patch.dict(os.environ, {}, clear=True)
    def test_misconfigured(self):
        with pytest.raises(Exception) as excinfo:
            Coveralls()

        assert str(excinfo.value) == 'You have to provide either repo_token in .coveralls.mock, or launch via Travis'


class Git(GitBasedTest):

    def test_git(self):
        cover = Coveralls(repo_token='xxx')
        git_info = cover.git_info()
        commit_id = git_info['git']['head'].pop('id')

        assert re.match(r'^[a-f0-9]{40}$', commit_id)
        assert git_info == {'git': {
            'head': {
                'committer_email': 'me@here.com',
                'author_email': 'me@here.com',
                'author_name': 'Guido',
                'message': 'first commit',
                'committer_name': 'Guido',
            },
            'remotes': [{
                'url': 'https://github.com/username/Hello-World.git',
                'name': 'origin'
            }],
            'branch': 'master'
        }}


class ReporterTest(unittest.TestCase):

    def setUp(self):
        os.chdir(join(dirname(dirname(__file__)), 'example'))
        sh.rm('-f', '.coverage')
        sh.rm('-f', 'extra.py')
        self.cover = Coveralls(repo_token='xxx')

    def test_reporter(self):
        sh.coverage('run', 'runtests.py')
        assert self.cover.get_coverage() == [{
            'source': '# coding: utf-8\n\n\ndef hello():\n    print(\'world\')\n\n\nclass Foo(object):\n    """ Bar """\n\n\ndef baz():\n    print(\'this is not tested\')',
            'name': 'project.py',
            'coverage': [None, None, None, 1, 1, None, None, 1, None, None, None, 1, 0]}, {
            'source': "# coding: utf-8\nfrom project import hello\n\nif __name__ == '__main__':\n    hello()",
            'name': 'runtests.py', 'coverage': [None, 1, None, 1, 1]}]

    def test_missing_file(self):
        sh.echo('print "Python rocks!"', _out="extra.py")
        sh.coverage('run', 'extra.py')
        sh.rm('-f', 'extra.py')
        assert self.cover.get_coverage() == []

    def test_not_python(self):
        sh.echo('print "Python rocks!"', _out="extra.py")
        sh.coverage('run', 'extra.py')
        sh.echo("<h1>This isn't python!</h1>", _out="extra.py")
        assert self.cover.get_coverage() == []


@patch('coveralls.api.requests')
class WearTest(unittest.TestCase):

    def setup_mock(self, mock_requests):
        self.expected_json = {'url': 'https://coveralls.io/jobs/5869', 'message': 'Job #7.1 - 44.58% Covered'}
        mock_requests.post.return_value.json.return_value = self.expected_json

    def test_wet_run(self, mock_requests):
        self.setup_mock(mock_requests)
        result = Coveralls(repo_token='xxx').wear(dry_run=False)
        assert result == self.expected_json

    def test_dry_run(self, mock_requests):
        self.setup_mock(mock_requests)
        result = Coveralls(repo_token='xxx').wear(dry_run=True)
        assert result == {}

    @patch.object(log, 'debug')
    def test_repo_token_in_not_compromised_verbose(self, mock_logger, mock_requests):
        self.setup_mock(mock_requests)
        result = Coveralls(repo_token='xxx').wear(dry_run=True)
        assert 'xxx' not in mock_logger.call_args[0][0]

    def test_coveralls_unavailable(self, mock_requests):
        mock_requests.post.return_value.json.side_effect = ValueError
        mock_requests.post.return_value.status_code = 500
        mock_requests.post.return_value.text = '<html>Http 1./1 500</html>'
        result = Coveralls(repo_token='xxx').wear()
        assert result == {'message': 'Failure to submit data. Response [500]: <html>Http 1./1 500</html>'}

    @patch('coveralls.reporter.CoverallReporter.report')
    def test_no_coverage(self, report_files, mock_requests):
        report_files.side_effect = coverage.CoverageException('No data to report')
        self.setup_mock(mock_requests)
        result = Coveralls(repo_token='xxx').wear()
        assert result == {'message': 'Failure to gather coverage: No data to report'}