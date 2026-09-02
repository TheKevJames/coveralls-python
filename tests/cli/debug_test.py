import os
from unittest import mock

import pytest

import coveralls.cli
from tests.cli.conftest import coveralls_kwargs


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch.object(coveralls.cli.log, 'info')
@mock.patch.object(coveralls.Coveralls, 'wear')
def test_debug(mock_wear: mock.MagicMock, mock_log: mock.MagicMock) -> None:
    coveralls.cli.main(argv=['debug'])
    mock_wear.assert_called_with(dry_run=True)
    mock_log.assert_has_calls([mock.call('Testing coveralls-python...')])


@mock.patch.dict(os.environ, clear=True)
@mock.patch.object(coveralls.cli.log, 'info')
@mock.patch.object(coveralls.Coveralls, 'wear')
def test_debug_no_token(
    mock_wear: mock.MagicMock, mock_log: mock.MagicMock
) -> None:
    coveralls.cli.main(argv=['debug'])
    mock_wear.assert_called_with(dry_run=True)
    mock_log.assert_has_calls([mock.call('Testing coveralls-python...')])


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_debug_accepts_options_after_subcommand(
    mock_coveralls: mock.MagicMock,
) -> None:
    # Each command owns its options, so they are given after the command name
    # (a long-standing, load-bearing invocation for debug).
    coveralls.cli.main(argv=['debug', '--rcfile=coveragerc', '--host=h'])
    mock_coveralls.assert_called_with(
        False, **coveralls_kwargs(rcfile='coveragerc', host='h')
    )


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_debug_does_not_advertise_verbose() -> None:
    # debug always forces verbose, so it does not offer a redundant --verbose.
    with pytest.raises(SystemExit):
        coveralls.cli.main(argv=['debug', '--verbose'])
