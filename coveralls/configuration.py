import logging
import os
import pathlib
import re
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

TIMEOUT_FIELDS = ('timeout', 'connect_timeout', 'read_timeout')

# The config keys that belong in the JSON submitted to coveralls.io -- every
# job parameter the API accepts and lets the caller set. Everything else in the
# config (base_dir, src_dir, config_file, the timeout family, ...) controls
# local client behaviour and must never be sent: the uploaded payload already
# includes every source file, so leaking client-only settings is both noise and
# a needless disclosure.
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
        config['coveralls_host'] = host
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

    # yaml.safe_load() returns None for an empty or comment-only file.
    return yaml.safe_load(content) or {}


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


def resolve(
    config_filename: str,
    overrides: dict[str, Any],
    *,
    token_required: bool = True,
) -> dict[str, Any]:
    """
    Resolve configuration from every source into a single merged config.

    Precedence (later wins): CI environment, ``COVERALLS_*`` env vars, the
    config file, then explicit overrides (e.g. CLI flags).

    ``token_required`` is not a config value read from any of those sources: it
    is a guard against accidental tokenless uploads, calculated here from the
    caller's ``token_required`` argument (the CLI derives it from the
    ``--debug``/``--output`` flags) and waived automatically on a CI service
    that authenticates uploads itself. A ``token_required`` key in the config
    file or environment is therefore ignored.
    """
    cleaned = {
        key: value for key, value in overrides.items() if value is not None
    }
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
    merged.setdefault('service_name', DEFAULT_SERVICE_NAME)
    merged.setdefault('coveralls_host', DEFAULT_HOST)
    # parallel is a payload field: normalize it only when a source set it, so
    # an unset value is omitted while an explicit parallel: false is forwarded.
    if 'parallel' in merged:
        merged['parallel'] = bool(merged['parallel'])
    merged['skip_ssl_verify'] = bool(merged.get('skip_ssl_verify'))
    for name in TIMEOUT_FIELDS:
        if name in merged:
            merged[name] = _validate_timeout(name, merged[name])

    return merged
