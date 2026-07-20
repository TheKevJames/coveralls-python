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

# CI services that authenticate coverage uploads themselves, so a Coveralls
# repo token is not required when running on them.
TOKENLESS_CI_SERVICES = frozenset({'travis-ci'})

# requests has no wall-clock "total" timeout: a scalar applies separately to
# the connect and read phases. We always resolve an explicit (connect, read)
# tuple so a stalled endpoint can never hang the CLI indefinitely.
DEFAULT_CONNECT_TIMEOUT = 10
DEFAULT_READ_TIMEOUT = 60

# Fields sent to the coveralls.io API -- every job parameter the /jobs endpoint
# accepts and lets the caller set. Everything else on Config controls local
# client behaviour and must never enter the submitted payload.
# See https://docs.coveralls.io/api-jobs-endpoint (service_build_url and
# service_branch are not in that table but are populated from CI and accepted;
# git and source_files are computed elsewhere, not sourced from config).
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
    'run_at',
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
    # None means "unset"; an explicit True/False is forwarded to the API so a
    # caller can positively mark a job as non-parallel.
    parallel: bool | None = None
    # No CI/env loader populates run_at; it is a caller-only field, set via the
    # config file or a Coveralls() kwarg, and forwarded because the API accepts
    # it (a job timestamp, per the /jobs endpoint).
    run_at: str | None = None

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
        # Include a field when it is set to anything other than None: an
        # explicitly-falsey value (parallel=False, a numeric 0 job id) is a
        # real choice and must be forwarded; only unset fields are dropped.
        return {
            name: value
            for name in PAYLOAD_FIELDS
            if (value := getattr(self, name)) is not None
        }


_FIELD_NAMES = frozenset(f.name for f in dataclasses.fields(Config))

# Config keys (in the config file or as Coveralls() kwargs) that were renamed
# for naming consistency. The old spelling still works but warns, mirroring the
# deprecated CLI flag aliases.
# Permanent alternate spellings accepted in the config file and as Coveralls()
# keyword arguments. Both the canonical name and the alias are long-term
# supported and neither warns: ``coveralls_host`` reads more clearly in a
# .coveralls.yml, while ``host`` matches the ``COVERALLS_HOST`` env var and
# ``--host`` flag.
ALIASES = {
    'coveralls_host': 'host',
}

# Renamed keys still accepted for backwards-compatibility but deprecated: they
# warn and will be removed in a future release.
DEPRECATED_KEYS = {
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
    default apply) plus a partial config of service-identifying fields.
    """
    env = os.environ
    if env.get('APPVEYOR'):
        return 'appveyor', {
            'service_job_id': env.get('APPVEYOR_BUILD_ID'),
            'service_pull_request': env.get('APPVEYOR_PULL_REQUEST_NUMBER'),
        }
    if env.get('BUILDKITE'):
        return 'buildkite', {
            'service_job_id': env.get('BUILDKITE_JOB_ID'),
            'service_pull_request': _parse_pr_number(
                env.get('BUILDKITE_PULL_REQUEST'),
            ),
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
            'service_pull_request': _parse_pr_number(
                env.get('TRAVIS_PULL_REQUEST'),
            ),
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


def _from_ci_environment(
    name: str | None, fields: dict[str, Any],
) -> dict[str, Any]:
    # As defined at the bottom of
    # https://docs.coveralls.io/supported-ci-services there are a few env vars
    # that support any arbitrary CI. We load them first and allow the more
    # specific service to overwrite job/number/pr, but the generic CI_NAME
    # takes precedence over the service's default name.
    config = _from_generic_ci_environment()

    if name:
        config.setdefault('service_name', name)

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
        'COVERALLS_BASE_DIR': 'base_dir',
        'COVERALLS_CONNECT_TIMEOUT': 'connect_timeout',
        'COVERALLS_FLAG_NAME': 'flag_name',
        'COVERALLS_RCFILE': 'rcfile',
        'COVERALLS_READ_TIMEOUT': 'read_timeout',
        'COVERALLS_REPO_TOKEN': 'repo_token',
        'COVERALLS_SERVICE_JOB_ID': 'service_job_id',
        'COVERALLS_SERVICE_JOB_NUMBER': 'service_job_number',
        'COVERALLS_SERVICE_NAME': 'service_name',
        'COVERALLS_SERVICE_NUMBER': 'service_number',
        'COVERALLS_SRC_DIR': 'src_dir',
        'COVERALLS_TIMEOUT': 'timeout',
    }
    for var, key in fields.items():
        value = os.environ.get(var)
        if value:
            config[key] = value

    return config


def _canonicalize_keys(
    data: Mapping[str, Any], *, source: str,
) -> dict[str, Any]:
    """
    Map alias/deprecated keys to their canonical names.

    Permanent aliases are mapped silently; deprecated keys additionally warn.
    An explicit canonical key in the same source always takes precedence.
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        canonical = ALIASES.get(key) or DEPRECATED_KEYS.get(key)
        if canonical is None:
            result[key] = value
            continue
        if key in DEPRECATED_KEYS:
            log.warning(
                '%r is deprecated and will be removed in a future release; '
                'use %r instead (in %s).', key, canonical, source,
            )
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

    data = _canonicalize_keys(
        yaml.safe_load(content) or {}, source=config_filename,
    )
    return _filter_known(data, source=config_filename)


def resolve(
    config_filename: str,
    overrides: Mapping[str, Any],
    *,
    token_required: bool = True,
) -> Config:
    """
    Resolve configuration from all sources into a single typed Config.

    Precedence (later wins): CI environment, ``COVERALLS_*`` env vars, the
    config file, then explicit overrides (e.g. CLI flags).

    ``token_required`` is not a config value read from any of those sources: it
    is a guard against accidental tokenless uploads, calculated here from the
    caller's ``token_required`` argument (the CLI derives it from the
    ``--debug``/``--output`` flags) and waived automatically on a CI service
    that authenticates uploads itself. A ``token_required`` key in the config
    file or environment is therefore ignored.
    """
    overrides = _canonicalize_keys(overrides, source='arguments')
    cleaned = _filter_known(
        {
            key: value for key, value in overrides.items()
            if value is not None
        },
        source='arguments',
    )
    name, fields = _detect_ci()

    partials = [
        _from_ci_environment(name, fields),
        _from_environment(),
        _from_file(config_filename),
        cleaned,
    ]

    merged: dict[str, Any] = {}
    for part in partials:
        merged.update(part)
    merged['token_required'] = (
        token_required and name not in TOKENLESS_CI_SERVICES
    )
    # Coerce the boolean flags: a config file may carry a non-bool (e.g. a
    # quoted ``parallel: "yes"``), which must not reach the API or a client
    # toggle as a stray string.
    for flag in ('parallel', 'skip_ssl_verify'):
        if flag in merged:
            merged[flag] = bool(merged[flag])

    return Config(**merged)
