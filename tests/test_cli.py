# coding: utf-8
import os

from mock import patch, call
import pytest

import coveralls
from coveralls.api import CoverallsException
import coveralls.cli


@patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@patch.object(coveralls.cli.log, 'info')
@patch.object(coveralls.Coveralls, 'wear')
def test_debug(mock_wear, mock_log):
    coveralls.cli.main(argv=['debug'])
    mock_wear.assert_called_with(dry_run=True)
    mock_log.assert_has_calls([call("Testing coveralls-python...")])


@patch.object(coveralls.cli.log, 'info')
@patch.object(coveralls.Coveralls, 'wear')
@patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_real(mock_wear, mock_log):
    coveralls.cli.main(argv=[])
    mock_wear.assert_called_with()
    mock_log.assert_has_calls([call("Submitting coverage to coveralls.io..."), call("Coverage submitted!")])


@patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@patch('coveralls.cli.Coveralls')
def test_rcfile(mock_coveralls):
    coveralls.cli.main(argv=['--rcfile=coveragerc'])
    mock_coveralls.assert_called_with(config_file='coveragerc')

exc = CoverallsException('bad stuff happened')

@patch.object(coveralls.cli.log, 'error')
@patch.object(coveralls.Coveralls, 'wear', side_effect=exc)
@patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_exception(mock_coveralls, mock_log):
    coveralls.cli.main(argv=[])
    mock_log.assert_has_calls([call(exc)])
