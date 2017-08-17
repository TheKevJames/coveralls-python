# coding: utf-8
import os

from mock import patch, call

import coveralls
from coveralls.api import CoverallsException
import coveralls.cli


@patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@patch.object(coveralls.cli.log, 'info')
@patch.object(coveralls.Coveralls, 'wear')
def test_debug(mock_wear, mock_log):
    coveralls.cli.main(argv=['debug'])
    mock_wear.assert_called_with(dry_run=True)
    mock_log.assert_has_calls([call('Testing coveralls-python...')])


@patch.object(coveralls.cli.log, 'info')
@patch.object(coveralls.Coveralls, 'wear')
def test_debug_no_token(mock_wear, mock_log):
    coveralls.cli.main(argv=['debug'])
    mock_wear.assert_called_with(dry_run=True)
    mock_log.assert_has_calls([call('Testing coveralls-python...')])


@patch.object(coveralls.cli.log, 'info')
@patch.object(coveralls.Coveralls, 'wear')
@patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_real(mock_wear, mock_log):
    coveralls.cli.main(argv=[])
    mock_wear.assert_called_with()
    mock_log.assert_has_calls([call('Submitting coverage to coveralls.io...'),
                               call('Coverage submitted!')])


@patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@patch('coveralls.cli.Coveralls')
def test_rcfile(mock_coveralls):
    coveralls.cli.main(argv=['--rcfile=coveragerc'])
    mock_coveralls.assert_called_with(True, config_file='coveragerc')

exc = CoverallsException('bad stuff happened')

@patch.object(coveralls.cli.log, 'error')
@patch.object(coveralls.Coveralls, 'wear', side_effect=exc)
@patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_exception(mock_coveralls, mock_log):
    try:
        coveralls.cli.main(argv=[])
        assert 0 == 1  # Should never reach this line
    except SystemExit:
        pass
    mock_log.assert_has_calls([call(exc)])


@patch.object(coveralls.Coveralls, 'save_report')
@patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_save_report_to_file(mock_coveralls):
    """Check save_report api usage."""

    coveralls.cli.main(argv=['--output=test.log'])
    mock_coveralls.assert_called_with('test.log')


@patch.object(coveralls.Coveralls, 'save_report')
def test_save_report_to_file_no_token(mock_coveralls):
    """Check save_report api usage when token is not set."""

    coveralls.cli.main(argv=['--output=test.log'])
    mock_coveralls.assert_called_with('test.log')
