import datetime
import os
import unittest.mock

import pytest

from coveralls.configuration import resolve
from coveralls.configuration.helpers import default_run_at


pytestmark = pytest.mark.usefixtures('isolate_cwd')

# A concrete run_at, in the space-separated form the /jobs endpoint documents.
FIXED = '2013-02-18 00:52:48 -0800'


@unittest.mock.patch.dict(
    os.environ, {'COVERALLS_RUN_AT': FIXED}, clear=True,
)
def test_run_at_read_from_environment() -> None:
    assert resolve({}).run_at == FIXED


@unittest.mock.patch.dict(
    os.environ, {'COVERALLS_RUN_AT': FIXED}, clear=True,
)
def test_run_at_override_wins_over_environment() -> None:
    assert resolve({'run_at': '2020-01-01 00:00:00 +0000'}).run_at == (
        '2020-01-01 00:00:00 +0000'
    )


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_run_at_defaults_to_now_when_unset() -> None:
    # No env/file/kwarg source: resolve() fills a current RFC 3339 timestamp so
    # the payload always carries a run_at, matching the official reporter.
    run_at = resolve({}).run_at
    assert run_at is not None
    # fromisoformat round-trips any RFC 3339 value default_run_at emits, and a
    # tz offset is always present (the official reporter's format includes it).
    assert datetime.datetime.fromisoformat(run_at).tzinfo is not None


def test_default_run_at_is_rfc3339_with_offset() -> None:
    parsed = datetime.datetime.fromisoformat(default_run_at())
    assert parsed.tzinfo is not None
    assert parsed.microsecond == 0
