import codecs
import json
import logging
import os
import pathlib
import re

import coverage
import requests

from .configuration import Config
from .configuration import resolve
from .exception import CoverallsException
from .git import git_info
from .reporter import CoverallReporter


log = logging.getLogger('coveralls.api')


class Coveralls:
    # pylint: disable=too-many-public-methods
    config_filename = '.coveralls.yml'

    def __init__(self, token_required=True, **kwargs):
        """
        Initialize the main Coveralls collection entrypoint.

        Keyword arguments are treated as explicit config overrides (highest
        precedence) and must be valid :class:`Config` fields, e.g.:

        * repo_token
          The secret token for your repository, found at the bottom of your
          repository's page on Coveralls.

        * service_name
          The CI service or other environment in which the test suite was run.
          This can be anything, but certain services have special features
          (travis-ci, travis-pro, or coveralls-ruby).

        * service_job_id
          A unique identifier of the job on the service specified by
          service_name.
        """
        self._data = None

        overrides = kwargs.copy()
        overrides['token_required'] = token_required
        self.config: Config = resolve(self.config_filename, overrides)

        self.ensure_token()

    def ensure_token(self):
        if self.config.repo_token or not self.config.token_required:
            return

        if os.environ.get('GITHUB_ACTIONS'):
            raise CoverallsException(
                'Running on Github Actions but GITHUB_TOKEN is not set. Add '
                '"env: GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}" to your '
                'step config.',
            )

        raise CoverallsException(
            'Not on TravisCI. You have to provide either repo_token in '
            f'{self.config_filename} or set the COVERALLS_REPO_TOKEN env var.',
        )

    def merge(self, path):
        reader = codecs.getreader('utf-8')
        with open(path, 'rb') as fh:
            extra = json.load(reader(fh))
            self.create_data(extra)

    def wear(self, dry_run=False):
        json_string = self.create_report()
        if dry_run:
            return {}
        return self.submit_report(json_string)

    def submit_report(self, json_string):
        endpoint = f'{self.config.host.rstrip("/")}/api/v1/jobs'
        verify = not self.config.skip_ssl_verify
        timeout = self.config.request_timeout
        try:
            response = requests.post(
                endpoint, files={'json_file': json_string}, verify=verify,
                timeout=timeout,
            )
        except requests.exceptions.Timeout as e:
            raise CoverallsException(
                f'Timed out submitting coverage to {endpoint} '
                f'(connect={timeout[0]}s, read={timeout[1]}s)',
            ) from e

        if response.status_code == 422:
            if self.config.service_name.startswith('github'):
                print(
                    'Received 422 submitting job via Github Actions. By '
                    'default, coveralls-python uses the "github" service '
                    'name, which requires you to set the $GITHUB_TOKEN '
                    'environment variable. If you want to use a '
                    'COVERALLS_REPO_TOKEN instead, please manually override '
                    '$COVERALLS_SERVICE_NAME to "github-actions". For more '
                    'info, see https://coveralls-python.readthedocs.io/en'
                    '/latest/usage/configuration.html#github-actions-support',
                )

        try:
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            raise CoverallsException(
                f'Could not submit coverage: {e}',
            ) from e

        return data

    # https://docs.coveralls.io/parallel-build-webhook
    def parallel_finish(self):
        payload = {'payload': {'status': 'done'}}

        # required args
        if self.config.repo_token:
            payload['repo_token'] = self.config.repo_token
        if self.config.service_number:
            payload['payload']['build_num'] = self.config.service_number

        # service-specific parameters
        if os.environ.get('GITHUB_REPOSITORY'):
            # Github Actions only
            payload['repo_name'] = os.environ.get('GITHUB_REPOSITORY')

        endpoint = f'{self.config.host.rstrip("/")}/webhook'
        verify = not self.config.skip_ssl_verify
        timeout = self.config.request_timeout
        try:
            response = requests.post(
                endpoint, json=payload, verify=verify, timeout=timeout,
            )
        except requests.exceptions.Timeout as e:
            raise CoverallsException(
                f'Timed out finishing parallel jobs at {endpoint} '
                f'(connect={timeout[0]}s, read={timeout[1]}s)',
            ) from e
        try:
            response.raise_for_status()
            response = response.json()
        except Exception as e:
            raise CoverallsException(
                f'Parallel finish failed: {e}',
            ) from e

        if 'error' in response:
            exc = response['error']
            raise CoverallsException(f'Parallel finish failed: {exc}')

        if 'done' not in response or not response['done']:
            raise CoverallsException('Parallel finish failed')

        return response

    def create_report(self):
        """Generate json dumped report for coveralls api."""
        data = self.create_data()
        try:
            json_string = json.dumps(data)
        except UnicodeDecodeError:
            log.exception('ERROR: While preparing JSON:')
            self.debug_bad_encoding(data)
            raise

        log_string = re.sub(
            r'"repo_token": "(.+?)"',
            '"repo_token": "[secure]"',
            json_string,
        )
        log.debug(log_string)
        log.debug('==\nReporting %s files\n==\n', len(data['source_files']))
        for source_file in data['source_files']:
            log.debug(
                '%s - %d/%d', source_file['name'],
                sum(filter(None, source_file['coverage'])),
                len(source_file['coverage']),
            )
        return json_string

    def save_report(self, file_path):
        """Write coveralls report to file."""
        try:
            report = self.create_report()
        except coverage.CoverageException:
            log.exception('Failure to gather coverage:')
        else:
            pathlib.Path(file_path).write_text(report)

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
        self._data.update(self.config.to_payload())
        if extra:
            if 'source_files' in extra:
                self._data['source_files'].extend(extra['source_files'])
            else:
                log.warning(
                    'No data to be merged; does the json file contain '
                    '"source_files" data?',
                )

        return self._data

    def get_coverage(self):
        work = coverage.coverage(config_file=self.config.rcfile)
        work.load()
        work.get_data()

        return CoverallReporter(
            work, self.config.base_dir, self.config.src_dir,
        ).coverage

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
            log.error(
                'HINT: Following files cannot be decoded properly into '
                'unicode. Check their content: %s',
                ', '.join(at_fault_files),
            )
