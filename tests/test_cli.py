# coding: utf-8
import os

from mock import patch, call

import coveralls
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
