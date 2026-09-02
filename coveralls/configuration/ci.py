import os
import re
from typing import Any

# Trailing integer, e.g. the number at the end of a pull-request URL or path.
NUMBER_REGEX = re.compile(r'(\d+)$')

# CI services that authenticate coverage uploads themselves, so a Coveralls
# repo token is not required when running on them.
TOKENLESS_CI_SERVICES = frozenset({'travis-ci'})


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
        os.environ.get('CI_PULL_REQUEST')
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
                env.get('BUILDKITE_PULL_REQUEST')
            ),
        }
    if env.get('CIRCLECI'):
        return 'circleci', {
            'service_job_id': env.get('CIRCLE_NODE_INDEX'),
            'service_number': (
                env.get('CIRCLE_WORKFLOW_ID') or env.get('CIRCLE_BUILD_NUM')
            ),
            'service_pull_request': _parse_pr_number(
                env.get('CI_PULL_REQUEST')
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
                env.get('CI_PULL_REQUEST')
            ),
        }
    if env.get('TRAVIS'):
        return 'travis-ci', {
            'service_job_id': env.get('TRAVIS_JOB_ID'),
            'service_pull_request': _parse_pr_number(
                env.get('TRAVIS_PULL_REQUEST')
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
    name: str | None, fields: dict[str, Any]
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
