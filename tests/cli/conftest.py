import json
import logging
import os
from typing import Any
from unittest import mock

import pytest

import coveralls.cli


EXC = RuntimeError('bad stuff happened')


# Resolve the repo's example dir from this module (tests/cli/conftest.py), so
# the upload tests can reach example/example.json regardless of cwd.
_REPO_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(__file__)),
)
EXAMPLE_DIR = os.path.join(_REPO_ROOT, 'example')


# The Config override keys the CLI always forwards to Coveralls(), derived
# from _make_coveralls itself (with a mocked constructor) rather than hand
# listed: a hardcoded mirror silently rots as options are added/removed, so
# instead the baseline tracks the real call site and cannot drift.
def _forwarded_override_keys() -> frozenset[str]:
    # pylint: disable=protected-access
    with mock.patch.object(coveralls.cli, 'Coveralls') as fake:
        coveralls.cli._make_coveralls(token_required=True)
    _, kwargs = fake.call_args
    return frozenset(kwargs)


_FORWARDED_OVERRIDE_KEYS = _forwarded_override_keys()


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
    so the constructor is always called with the full override set. The unset
    baseline is derived from _make_coveralls (see _forwarded_override_keys), so
    a newly added CLI option is asserted automatically without editing here.
    """
    kwargs: dict[str, Any] = {key: None for key in _FORWARDED_OVERRIDE_KEYS}
    kwargs.update(overrides)
    return kwargs
