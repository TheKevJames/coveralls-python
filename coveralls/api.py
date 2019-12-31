# coding: utf-8
import codecs
import json
import logging
import os
import re

import coverage
import requests

from .exception import CoverallsException
from .git import git_info
from .reporter import CoverallReporter


log = logging.getLogger('coveralls.api')


class Coveralls(object):
    config_filename = '.coveralls.yml'

    def __init__(self, token_required=True, service_name=None, **kwargs):
        """
        * repo_token
          The secret token for your repository, found at the bottom of your
          repository's page on Coveralls.

        * service_name
          The CI service or other environment in which the test suite was run.
          This can be anything, but certain services have special features
          (travis-ci, travis-pro, or coveralls-ruby).

        * [service_job_id]
          A unique identifier of the job on the service specified by
          service_name.
        """
        self._data = None
        self._coveralls_host = 'https://coveralls.io/'
        self._token_required = token_required

        self.config = self.load_config_from_file()
        self.config.update(kwargs)
        if service_name:
            self.config['service_name'] = service_name
        if self.config.get('coveralls_host'):
            self._coveralls_host = self.config['coveralls_host']
            del self.config['coveralls_host']

        self.load_config_from_environment()

        name, job, pr = self.load_config_from_ci_environment()
        self.config['service_name'] = self.config.get('service_name', name)
        if job:
            self.config['service_job_id'] = job
        if pr:
            self.config['service_pull_request'] = pr

        self.ensure_token()

    def ensure_token(self):
        if self.config.get('repo_token') or not self._token_required:
            return

        raise CoverallsException(
            'Not on TravisCI. You have to provide either repo_token in {} or '
            'set the COVERALLS_REPO_TOKEN env var.'.format(
                self.config_filename))

    @staticmethod
    def load_config_from_appveyor():
        pr = os.environ.get('APPVEYOR_PULL_REQUEST_NUMBER')
        return 'appveyor', os.environ.get('APPVEYOR_BUILD_ID'), pr

    @staticmethod
    def load_config_from_buildkite():
        pr = os.environ.get('BUILDKITE_PULL_REQUEST')
        if pr == 'false':
            pr = None
        return 'buildkite', os.environ.get('BUILDKITE_JOB_ID'), pr

    @staticmethod
    def load_config_from_circle():
        pr = os.environ.get('CI_PULL_REQUEST', '').split('/')[-1] or None
        return 'circle-ci', os.environ.get('CIRCLE_BUILD_NUM'), pr

    @staticmethod
    def load_config_from_github():
        pr = None
        if os.environ.get('GITHUB_REF', '').startswith('refs/pull/'):
            pr = os.environ.get('GITHUB_REF', '//').split('/')[2]
        return 'github-actions', None, pr

    @staticmethod
    def load_config_from_jenkins():
        pr = os.environ.get('CI_PULL_REQUEST', '').split('/')[-1] or None
        return 'jenkins', os.environ.get('BUILD_NUMBER'), pr

    @staticmethod
    def load_config_from_travis():
        pr = os.environ.get('TRAVIS_PULL_REQUEST')
        return 'travis-ci', os.environ.get('TRAVIS_JOB_ID'), pr

    @staticmethod
    def load_config_from_semaphore():
        pr = os.environ.get('PULL_REQUEST_NUMBER')
        return 'semaphore-ci', os.environ.get('SEMAPHORE_BUILD_NUMBER'), pr

    @staticmethod
    def load_config_from_unknown():
        return 'coveralls-python', None, None

    def load_config_from_ci_environment(self):
        if os.environ.get('APPVEYOR'):
            name, job, pr = self.load_config_from_appveyor()
        elif os.environ.get('BUILDKITE'):
            name, job, pr = self.load_config_from_buildkite()
        elif os.environ.get('CIRCLECI'):
            name, job, pr = self.load_config_from_circle()
        elif os.environ.get('GITHUB_ACTIONS'):
            name, job, pr = self.load_config_from_github()
        elif os.environ.get('JENKINS_HOME'):
            name, job, pr = self.load_config_from_jenkins()
        elif os.environ.get('TRAVIS'):
            self._token_required = False
            name, job, pr = self.load_config_from_travis()
        elif os.environ.get('SEMAPHORE'):
            name, job, pr = self.load_config_from_semaphore()
        else:
            name, job, pr = self.load_config_from_unknown()
        return (name, job, pr)

    def load_config_from_environment(self):
        coveralls_host = os.environ.get('COVERALLS_HOST')
        if coveralls_host:
            self._coveralls_host = coveralls_host

        parallel = os.environ.get('COVERALLS_PARALLEL', '').lower() == 'true'
        if parallel:
            self.config['parallel'] = parallel

        repo_token = os.environ.get('COVERALLS_REPO_TOKEN')
        if repo_token:
            self.config['repo_token'] = repo_token

        service_name = os.environ.get('COVERALLS_SERVICE_NAME')
        if service_name:
            self.config['service_name'] = service_name

        flag_name = os.environ.get('COVERALLS_FLAG_NAME')
        if flag_name:
            self.config['flag_name'] = flag_name

    def load_config_from_file(self):
        try:
            with open(os.path.join(os.getcwd(),
                                   self.config_filename)) as config:
                try:
                    import yaml
                    return yaml.safe_load(config)
                except ImportError:
                    log.warning('PyYAML is not installed, skipping %s.',
                                self.config_filename)
        except (OSError, IOError):
            log.debug('Missing %s file. Using only env variables.',
                      self.config_filename)

        return {}

    def merge(self, path):
        reader = codecs.getreader('utf-8')
        with open(path, 'rb') as fh:
            extra = json.load(reader(fh))
            self.create_data(extra)

    def wear(self, dry_run=False):
        json_string = self.create_report()
        if dry_run:
            return {}

        endpoint = '{}/api/v1/jobs'.format(self._coveralls_host.rstrip('/'))
        verify = not bool(os.environ.get('COVERALLS_SKIP_SSL_VERIFY'))
        response = requests.post(endpoint, files={'json_file': json_string},
                                 verify=verify)
        try:
            response.raise_for_status()
            return response.json()
        except Exception as e:
            raise CoverallsException('Could not submit coverage: {}'.format(e))

    def create_report(self):
        """Generate json dumped report for coveralls api."""
        data = self.create_data()
        try:
            json_string = json.dumps(data)
        except UnicodeDecodeError as e:
            log.error('ERROR: While preparing JSON:', exc_info=e)
            self.debug_bad_encoding(data)
            raise

        log_string = re.sub(r'"repo_token": "(.+?)"',
                            '"repo_token": "[secure]"', json_string)
        log.debug(log_string)
        log.debug('==\nReporting %s files\n==\n', len(data['source_files']))
        for source_file in data['source_files']:
            log.debug('%s - %s/%s', source_file['name'],
                      sum(filter(None, source_file['coverage'])),
                      len(source_file['coverage']))
        return json_string

    def save_report(self, file_path):
        """Write coveralls report to file."""
        try:
            report = self.create_report()
        except coverage.CoverageException as e:
            log.error('Failure to gather coverage:', exc_info=e)
        else:
            with open(file_path, 'w') as report_file:
                report_file.write(report)

    def create_data(self, extra=None):
        r"""
        Generate object for api.

        Example json:
            {
                "service_job_id": "1234567890",
                "service_name": "travis-ci",
                "source_files": [
                    {
                        "name": "example.py",
                        "source": "def four\n  4\nend",
                        "coverage": [null, 1, null]
                    },
                    {
                        "name": "two.py",
                        "source": "def seven\n  eight\n  nine\nend",
                        "coverage": [null, 1, 0, null]
                    }
                ],
                "parallel": True
            }
        """
        if self._data:
            return self._data

        self._data = {'source_files': self.get_coverage()}
        self._data.update(git_info())
        self._data.update(self.config)
        if extra:
            if 'source_files' in extra:
                self._data['source_files'].extend(extra['source_files'])
            else:
                log.warning('No data to be merged; does the json file contain '
                            '"source_files" data?')

        return self._data

    def get_coverage(self):
        config_file = self.config.get('config_file', True)
        workman = coverage.coverage(config_file=config_file)
        workman.load()

        if hasattr(workman, '_harvest_data'):
            workman._harvest_data()  # pylint: disable=W0212
        else:
            workman.get_data()

        return CoverallReporter(workman, workman.config).coverage

    @staticmethod
    def debug_bad_encoding(data):
        """Let's try to help user figure out what is at fault."""
        at_fault_files = set()
        for source_file_data in data['source_files']:
            for value in source_file_data.values():
                try:
                    json.dumps(value)
                except UnicodeDecodeError:
                    at_fault_files.add(source_file_data['name'])

        if at_fault_files:
            log.error('HINT: Following files cannot be decoded properly into '
                      'unicode. Check their content: %s',
                      ', '.join(at_fault_files))
