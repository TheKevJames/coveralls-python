import os
from unittest import mock

import coveralls.cli
from tests.cli.conftest import coveralls_kwargs


@mock.patch.object(coveralls.Coveralls, 'save_report')
@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_save_report_to_file(mock_coveralls: mock.MagicMock) -> None:
    """Check save_report api usage."""
    coveralls.cli.main(argv=['save', 'test.log'])
    mock_coveralls.assert_called_with('test.log')


@mock.patch.dict(os.environ, clear=True)
@mock.patch.object(coveralls.Coveralls, 'save_report')
def test_save_report_to_file_no_token(mock_coveralls: mock.MagicMock) -> None:
    """Check save_report api usage when token is not set."""
    coveralls.cli.main(argv=['save', 'test.log'])
    mock_coveralls.assert_called_with('test.log')


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch.object(coveralls.cli.log, 'warning')
@mock.patch.object(coveralls.Coveralls, 'save_report')
def test_save_report_deprecated_output_warns(
    mock_save: mock.MagicMock, mock_warning: mock.MagicMock
) -> None:
    coveralls.cli.main(argv=['--output=test.log'])
    mock_save.assert_called_with('test.log')
    mock_warning.assert_called_once_with(
        '%s is deprecated and will be removed in a future release; use %s '
        'instead.',
        '--output',
        'coveralls save FILE',
    )


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_submit_family_accepts_merge_and_parallel(
    mock_coveralls: mock.MagicMock,
) -> None:
    # save/debug build a report, so they honour the submit-only modifiers.
    coveralls.cli.main(argv=['save', 'o', '--parallel', '--merge=extra.json'])
    mock_coveralls.assert_called_with(False, **coveralls_kwargs(parallel=True))
    mock_coveralls.return_value.merge.assert_called_once_with('extra.json')
    mock_coveralls.return_value.save_report.assert_called_once_with('o')
