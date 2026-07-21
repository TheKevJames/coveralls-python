import json
import logging
import os
import pathlib
import re
from typing import Any

import coverage
import requests
import urllib3.exceptions
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .configuration import Config
from .configuration import resolve
from .git import git_info
from .reporter import CoverallReporter


log = logging.getLogger('coveralls.api')

# Transient failures worth retrying: server-side 5xx and rate limiting (429).
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})
# urllib3's default allowed_methods excludes POST (non-idempotent); every call
# we make is a POST, so we must opt POST in explicitly or nothing retries.
RETRY_METHODS = frozenset({'POST'})
# Exponential backoff with jitter. backoff_factor sets the base delay
# (0.5, 1, 2, 4, ... seconds), backoff_jitter adds up to this many seconds of
# randomness to spread out retries, and backoff_max caps any single wait.
RETRY_BACKOFF_FACTOR = 0.5
RETRY_BACKOFF_JITTER = 0.5
RETRY_BACKOFF_MAX = 60


def _build_session(retries: int) -> requests.Session:
    """
    Build a requests Session that retries transient HTTP failures.

    With ``retries=0`` this is equivalent to a plain ``requests`` call: a
    single attempt is made and connect/read timeouts surface as before.
    ``raise_on_status=False`` keeps the final response (even a 5xx) flowing
    back to the caller so the existing status handling stays in charge.
    """
    # urllib3 treats read=0 and read=False differently: read=0 raises
    # MaxRetryError on a read timeout (which requests remaps to a bare
    # ConnectionError), while read=False lets the ReadTimeoutError propagate as
    # a requests Timeout. Mirror requests' own default (Retry(0, read=False))
    # so the no-retry path still surfaces read timeouts as TimeoutError.
    read = retries or False
    retry = Retry(
        total=retries, connect=retries, read=read, status=retries,
        other=retries,
        status_forcelist=RETRY_STATUSES,
        allowed_methods=RETRY_METHODS,
        backoff_factor=RETRY_BACKOFF_FACTOR,
        backoff_jitter=RETRY_BACKOFF_JITTER,
        backoff_max=RETRY_BACKOFF_MAX,
        # Ignore Retry-After and always use our own bounded backoff: a server
        # can send an arbitrarily large Retry-After (e.g. 3600s), and urllib3
        # only started clamping it -- to 6 hours -- in 2.6.3, so on our
        # supported range it is otherwise unbounded and could hang CI for
        # hours. 429/503 are still retried; only the sleep length differs.
        respect_retry_after_header=False,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def _caused_by_timeout(exc: requests.exceptions.RequestException) -> bool:
    """
    Report whether a request failure was ultimately a timeout.

    A single timeout raises a requests ``Timeout`` directly, but a timeout that
    exhausts its retries surfaces as a ``ConnectionError`` wrapping a urllib3
    ``MaxRetryError`` whose ``reason`` is a urllib3 ``TimeoutError``; unwrap
    that so both read the same to the caller.
    """
    if isinstance(exc, requests.exceptions.Timeout):
        return True
    reason = getattr(exc.args[0] if exc.args else None, 'reason', None)
    return isinstance(reason, urllib3.exceptions.TimeoutError)


class Coveralls:
    config_filename = '.coveralls.yml'

    def __init__(self, token_required: bool = True, **kwargs: Any) -> None:
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
        self._data: dict[str, Any] | None = None

        self.config: Config = resolve(
            self.config_filename, kwargs, token_required=token_required,
        )

        self.ensure_token()

    def ensure_token(self) -> None:
        if self.config.repo_token or not self.config.token_required:
            return

        if os.environ.get('GITHUB_ACTIONS'):
            raise RuntimeError(
                'Running on Github Actions but GITHUB_TOKEN is not set. Add '
                '"env: GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}" to your '
                'step config.',
            )

        raise RuntimeError(
            'No supported CI found and no repo token configured. You have to '
            f'provide either repo_token in {self.config_filename} or set the '
            'COVERALLS_REPO_TOKEN env var.',
        )

    def merge(self, path: str) -> None:
        extra = json.loads(pathlib.Path(path).read_text(encoding='utf-8'))
        self.create_data(extra)

    def wear(self, dry_run: bool = False) -> dict[str, Any]:
        json_string = self.create_report()
        if dry_run:
            return {}
        return self.submit_report(json_string)

    def _post(self, endpoint: str, **kwargs: Any) -> requests.Response:
        """
        POST to a coveralls endpoint, retrying transient failures.

        A transient failure that exhausts its retries surfaces as a
        connection/RetryError rather than a plain Timeout, so both are mapped
        to clear exceptions here (see :func:`_caused_by_timeout`).
        """
        verify = not self.config.skip_ssl_verify
        timeout = self.config.request_timeout
        # Each command makes a single POST, so there is no pooling benefit from
        # the session; it exists only to carry the retry adapter. Close it to
        # release the connection pool and avoid a ResourceWarning.
        try:
            with _build_session(self.config.retries) as session:
                return session.post(
                    endpoint, verify=verify, timeout=timeout, **kwargs,
                )
        except requests.exceptions.RequestException as e:
            if _caused_by_timeout(e):
                raise TimeoutError(
                    f'Request timeout: {endpoint} (timeout={timeout})',
                ) from e
            raise RuntimeError(f'Could not submit coverage: {e}') from e

    def submit_report(self, json_string: str) -> dict[str, Any]:
        endpoint = f'{self.config.host.rstrip("/")}/api/v1/jobs'
        response = self._post(endpoint, files={'json_file': json_string})

        if response.status_code == 422:
            if self.config.service_name.startswith('github'):
                log.warning(
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
            data: dict[str, Any] = response.json()
        except Exception as e:
            raise RuntimeError(
                f'Could not submit coverage: {e}',
            ) from e

        return data

    # https://docs.coveralls.io/parallel-build-webhook
    def parallel_finish(self) -> dict[str, Any]:
        payload: dict[str, Any] = {'payload': {'status': 'done'}}

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
        response = self._post(endpoint, json=payload)
        try:
            response.raise_for_status()
            data: dict[str, Any] = response.json()
        except Exception as e:
            raise RuntimeError(f'Could not submit coverage: {e}') from e

        if 'error' in data:
            exc = data['error']
            raise RuntimeError(f'Parallel finish failed: {exc}')

        if 'done' not in data or not data['done']:
            raise RuntimeError('Parallel finish failed')

        return data

    def create_report(self) -> str:
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

    def save_report(self, file_path: str) -> None:
        """Write coveralls report to file."""
        try:
            report = self.create_report()
        except coverage.CoverageException:
            log.exception('Failure to gather coverage:')
        else:
            pathlib.Path(file_path).write_text(report, encoding='utf-8')

    def create_data(
        self, extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
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

        self._data = {'source_files': self.get_coverage()} | git_info()
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

    def get_coverage(self) -> list[dict[str, Any]]:
        work = coverage.coverage(config_file=self.config.rcfile)
        work.load()
        work.get_data()

        return CoverallReporter(
            work, self.config.base_dir, self.config.src_dir,
        ).coverage

    @staticmethod
    def debug_bad_encoding(data: dict[str, Any]) -> None:
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
