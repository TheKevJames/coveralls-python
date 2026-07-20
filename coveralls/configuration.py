import dataclasses
import logging
import os
import pathlib
import re
from collections.abc import Mapping
from typing import Any

from .exception import CoverallsException


log = logging.getLogger('coveralls.configuration')

# Trailing integer, e.g. the number at the end of a pull-request URL or path.
NUMBER_REGEX = re.compile(r'(\d+)$')

DEFAULT_HOST = 'https://coveralls.io/'

# Used when no CI service is detected and none is configured explicitly.
DEFAULT_SERVICE_NAME = 'coveralls-python'

# requests has no wall-clock "total" timeout: a scalar applies separately to
# the connect and read phases. We always resolve an explicit (connect, read)
# tuple so a stalled endpoint can never hang the CLI indefinitely.
DEFAULT_CONNECT_TIMEOUT = 10
DEFAULT_READ_TIMEOUT = 60

# Fields sent to the coveralls.io API. Everything else on Config controls local
# client behaviour and must never enter the submitted payload.
PAYLOAD_FIELDS = (
    'repo_token',
    'service_name',
    'service_number',
    'service_job_id',
    'service_job_number',
    'service_pull_request',
    'service_branch',
    'service_build_url',
    'flag_name',
    'parallel',
)


@dataclasses.dataclass
class Config:
    # pylint: disable=too-many-instance-attributes
    """
    Fully resolved coveralls-python configuration.

    Fields fall into two groups. The :data:`PAYLOAD_FIELDS` are sent to the
    coveralls.io API via :meth:`to_payload`; every other field controls local
    client behaviour (where to send, how to talk to coverage.py, etc.) and is
    deliberately never included in the submitted payload.
    """

    # payload fields
    repo_token: str | None = None
    service_name: str = DEFAULT_SERVICE_NAME
    service_number: str | None = None
    service_job_id: str | None = None
    service_job_number: str | None = None
    service_pull_request: str | None = None
    service_branch: str | None = None
    service_build_url: str | None = None
    flag_name: str | None = None
    parallel: bool = False

    # client settings
    host: str = DEFAULT_HOST
    skip_ssl_verify: bool = False
    token_required: bool = True
    base_dir: str = ''
    src_dir: str = ''
    # True lets coverage.py auto-discover its config file; a str names one.
    rcfile: str | bool = True
    timeout: float | None = None
    connect_timeout: float | None = None
    read_timeout: float | None = None

    def __post_init__(self) -> None:
        self.timeout = self._validate_timeout('timeout', self.timeout)
        self.connect_timeout = self._validate_timeout(
            'connect_timeout', self.connect_timeout,
        )
        self.read_timeout = self._validate_timeout(
            'read_timeout', self.read_timeout,
        )

    @staticmethod
    def _validate_timeout(name: str, raw: Any) -> float | None:
        if raw is None:
            return None
        try:
            value = float(raw)
        except (TypeError, ValueError) as e:
            raise CoverallsException(
                f'Invalid {name} value {raw!r}: must be a number.',
            ) from e
        if value <= 0:
            raise CoverallsException(
                f'Invalid {name} value {raw!r}: must be greater than 0.',
            )
        return value

    @property
    def request_timeout(self) -> tuple[float, float]:
        """
        Resolve the (connect, read) tuple passed to ``requests``.

        A phase-specific value wins for its phase; otherwise the overall
        ``timeout`` applies; otherwise the phase default is used.
        """
        connect = self.connect_timeout
        if connect is None:
            connect = self.timeout
        if connect is None:
            connect = DEFAULT_CONNECT_TIMEOUT

        read = self.read_timeout
        if read is None:
            read = self.timeout
        if read is None:
            read = DEFAULT_READ_TIMEOUT

        return (connect, read)

    def to_payload(self) -> dict[str, Any]:
        """Build the subset of config that is submitted to the API."""
        return {
            name: value
            for name in PAYLOAD_FIELDS
            if (value := getattr(self, name))
        }


_FIELD_NAMES = frozenset(f.name for f in dataclasses.fields(Config))

# Config keys (in the config file or as Coveralls() kwargs) that were renamed
# for naming consistency. The old spelling still works but warns, mirroring the
# deprecated CLI flag aliases.
DEPRECATED_KEYS = {
    'coveralls_host': 'host',
    'config_file': 'rcfile',
}


def _parse_pr_number(value: str | None) -> str | None:
    """
    Extract the pull-request number from a CI-provided value.

    The value may be a bare integer, a path, or a full URL; per the Coveralls
    docs the PR number is the trailing integer (e.g. ``.../pull/42`` -> 42).
    All CI loaders that read a PR value share this single semantic.
    """
    matches = NUMBER_REGEX.findall(value or '')
    return matches[-1] if matches else None


def _from_generic_ci_environment() -> dict[str, Any]:
    # Inspired by the official client: coveralls-ruby in
    # lib/coveralls/configuration.rb
    # (set_standard_service_params_for_generic_ci).
    # The meaning of each var is clarified in:
    # https://github.com/lemurheavy/coveralls-public/issues/1558
    config = {
        'service_name': os.environ.get('CI_NAME'),
        'service_number': os.environ.get('CI_BUILD_NUMBER'),
        'service_build_url': os.environ.get('CI_BUILD_URL'),
        'service_job_id': os.environ.get('CI_JOB_ID'),
        'service_branch': os.environ.get('CI_BRANCH'),
    }

    config['service_pull_request'] = _parse_pr_number(
        os.environ.get('CI_PULL_REQUEST'),
    )

    return {key: value for key, value in config.items() if value}


def _detect_ci() -> tuple[str | None, dict[str, Any]]:
    # pylint: disable=too-many-return-statements
    """
    Detect the specific CI service and its service-identifying fields.

    Returns the service name (or None when no CI is detected, letting the
    Config default apply) plus a partial config. ``token_required`` may be
    present to waive the repo-token requirement (e.g. on TravisCI).
    """
    env = os.environ
    if env.get('APPVEYOR'):
        return 'appveyor', {
            'service_job_id': env.get('APPVEYOR_BUILD_ID'),
            'service_pull_request': env.get('APPVEYOR_PULL_REQUEST_NUMBER'),
        }
    if env.get('BUILDKITE'):
        pr = env.get('BUILDKITE_PULL_REQUEST')
        return 'buildkite', {
            'service_job_id': env.get('BUILDKITE_JOB_ID'),
            'service_pull_request': None if pr == 'false' else pr,
        }
    if env.get('CIRCLECI'):
        return 'circleci', {
            'service_job_id': env.get('CIRCLE_NODE_INDEX'),
            'service_number': (
                env.get('CIRCLE_WORKFLOW_ID') or env.get('CIRCLE_BUILD_NUM')
            ),
            'service_pull_request': _parse_pr_number(
                env.get('CI_PULL_REQUEST'),
            ),
        }
    if env.get('GITHUB_ACTIONS'):
        # See https://github.com/lemurheavy/coveralls-public/issues/1710
        # GitHub tokens and standard Coveralls tokens are almost but not quite
        # the same -- forcibly using GitHub's flow seems to be more stable.
        pr = None
        if env.get('GITHUB_REF', '').startswith('refs/pull/'):
            pr = env.get('GITHUB_REF', '//').split('/')[2]
        run_id = env.get('GITHUB_RUN_ID')
        return 'github', {
            'repo_token': env.get('GITHUB_TOKEN'),
            'service_job_id': run_id,
            'service_number': run_id,
            'service_pull_request': pr,
        }
    if env.get('JENKINS_HOME'):
        return 'jenkins', {
            'service_job_id': env.get('BUILD_NUMBER'),
            'service_pull_request': _parse_pr_number(
                env.get('CI_PULL_REQUEST'),
            ),
        }
    if env.get('TRAVIS'):
        return 'travis-ci', {
            'service_job_id': env.get('TRAVIS_JOB_ID'),
            'service_pull_request': env.get('TRAVIS_PULL_REQUEST'),
            'token_required': False,
        }
    if env.get('SEMAPHORE'):
        return 'semaphore-ci', {
            'service_job_id': (
                env.get('SEMAPHORE_JOB_UUID')  # Classic
                or env.get('SEMAPHORE_JOB_ID')  # 2.0
            ),
            'service_number': (
                env.get('SEMAPHORE_EXECUTABLE_UUID')  # Classic
                or env.get('SEMAPHORE_WORKFLOW_ID')  # 2.0
            ),
            'service_pull_request': (
                env.get('SEMAPHORE_BRANCH_ID')  # Classic
                or env.get('SEMAPHORE_GIT_PR_NUMBER')  # 2.0
            ),
        }
    return None, {}


def _from_ci_environment() -> dict[str, Any]:
    # As defined at the bottom of
    # https://docs.coveralls.io/supported-ci-services there are a few env vars
    # that support any arbitrary CI. We load them first and allow the more
    # specific service to overwrite job/number/pr, but the generic CI_NAME
    # takes precedence over the service's default name.
    config = _from_generic_ci_environment()

    name, fields = _detect_ci()
    if name:
        config.setdefault('service_name', name)

    token_required = fields.pop('token_required', None)
    if token_required is not None:
        config['token_required'] = token_required

    for key, value in fields.items():
        if value:
            config[key] = value

    return config


def _from_environment() -> dict[str, Any]:
    config: dict[str, Any] = {}

    host = os.environ.get('COVERALLS_HOST')
    if host:
        config['host'] = host
    if os.environ.get('COVERALLS_PARALLEL', '').lower() == 'true':
        config['parallel'] = True
    if os.environ.get('COVERALLS_SKIP_SSL_VERIFY'):
        config['skip_ssl_verify'] = True

    fields = {
        'COVERALLS_CONNECT_TIMEOUT': 'connect_timeout',
        'COVERALLS_FLAG_NAME': 'flag_name',
        'COVERALLS_READ_TIMEOUT': 'read_timeout',
        'COVERALLS_REPO_TOKEN': 'repo_token',
        'COVERALLS_SERVICE_JOB_ID': 'service_job_id',
        'COVERALLS_SERVICE_JOB_NUMBER': 'service_job_number',
        'COVERALLS_SERVICE_NAME': 'service_name',
        'COVERALLS_SERVICE_NUMBER': 'service_number',
        'COVERALLS_TIMEOUT': 'timeout',
    }
    for var, key in fields.items():
        value = os.environ.get(var)
        if value:
            config[key] = value

    return config


def _apply_deprecated_keys(
    data: Mapping[str, Any], *, source: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in data.items():
        canonical = DEPRECATED_KEYS.get(key)
        if canonical is None:
            result[key] = value
            continue
        log.warning(
            '%r is deprecated and will be removed in a future release; use '
            '%r instead (in %s).', key, canonical, source,
        )
        # An explicit canonical key in the same source takes precedence.
        if canonical not in data:
            result[canonical] = value
    return result


def _filter_known(data: Mapping[str, Any], *, source: str) -> dict[str, Any]:
    known = {}
    for key, value in data.items():
        if key in _FIELD_NAMES:
            known[key] = value
        else:
            log.warning(
                'Ignoring unknown config option %r from %s.', key, source,
            )
    return known


def _from_file(config_filename: str) -> dict[str, Any]:
    try:
        import yaml  # pylint: disable=import-outside-toplevel
    except ImportError:
        log.warning('PyYAML is not installed, skipping %s.', config_filename)
        return {}

    try:
        content = (pathlib.Path.cwd() / config_filename).read_text()
    except FileNotFoundError:
        log.debug(
            'Missing %s file. Using only env variables.', config_filename,
        )
        return {}

    data = _apply_deprecated_keys(
        yaml.safe_load(content) or {}, source=config_filename,
    )
    return _filter_known(data, source=config_filename)


def resolve(config_filename: str, overrides: Mapping[str, Any]) -> Config:
    """
    Resolve configuration from all sources into a single typed Config.

    Precedence (later wins): CI environment, ``COVERALLS_*`` env vars, the
    config file, then explicit overrides (e.g. CLI flags). ``token_required``
    is special: any source may waive the requirement but none may re-impose
    it, so it is AND-ed across sources rather than last-wins.
    """
    overrides = _apply_deprecated_keys(overrides, source='arguments')
    cleaned = {
        key: value for key,
        value in overrides.items() if value is not None
    }
    partials = [
        _from_ci_environment(),
        _from_environment(),
        _from_file(config_filename),
        cleaned,
    ]

    merged: dict[str, Any] = {}
    token_required = True
    for part in partials:
        part = part.copy()
        required = part.pop('token_required', None)
        if required is not None:
            token_required = token_required and required
        merged.update(part)
    merged['token_required'] = token_required

    return Config(**merged)
