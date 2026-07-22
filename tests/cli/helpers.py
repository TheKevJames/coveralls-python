import json
import logging
import os
from typing import Any

import pytest


EXC = RuntimeError('bad stuff happened')


# Resolve the repo's example dir from this module (tests/cli/helpers.py), so
# the upload tests can reach example/example.json regardless of cwd.
_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(__file__)),
)
EXAMPLE_DIR = os.path.join(_REPO_ROOT, 'example')


def github_finish_env() -> dict[str, str]:
    return {
        'GITHUB_ACTIONS': 'true',
        'GITHUB_REPOSITORY': 'test/repo',
        'GITHUB_TOKEN': 'xxx',
        'GITHUB_RUN_ID': '123456789',
        'GITHUB_RUN_NUMBER': '123',
    }


def req_json(request: Any) -> Any:
    return json.loads(request.body.decode('utf-8'))


def assert_logged_error(
    caplog: pytest.LogCaptureFixture, msg: str,
) -> None:
    """Assert _run_action logged exactly one error carrying exception `msg`.

    _run_action logs via log.exception, so the failing exception is recorded
    in the record's exc_info rather than the message; we inspect that.
    """
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errors) == 1
    record = errors[0]
    assert record.message == 'Error running coveralls'
    assert record.exc_info is not None
    assert str(record.exc_info[1]) == msg


def coveralls_kwargs(**overrides: Any) -> dict[str, Any]:
    """Expected Coveralls() override kwargs: everything unset (None) initially.

    The CLI forwards every value as-is and lets resolve() drop the unset ones,
    so the constructor is always called with the full override set.

    Keep this in sync with the CLI option set: a new forwarded option must be
    added here, otherwise every test that uses the default set will silently
    under-assert on it.
    """
    kwargs = {
        'rcfile': None,
        'service_name': None,
        'base_dir': None,
        'src_dir': None,
        'host': None,
        'parallel': None,
        'carryforward': None,
        'skip_ssl_verify': None,
        'timeout': None,
        'connect_timeout': None,
        'read_timeout': None,
        'retries': None,
    }
    kwargs.update(overrides)
    return kwargs
