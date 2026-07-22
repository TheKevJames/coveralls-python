import os
from unittest import mock

import pytest

import coveralls.cli
from tests.cli.conftest import EXAMPLE_DIR


@mock.patch.object(coveralls.Coveralls, 'submit_report')
@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_upload(mock_submit: mock.MagicMock) -> None:
    json_file = os.path.join(EXAMPLE_DIR, 'example.json')
    coveralls.cli.main(argv=['upload', json_file])
    with open(json_file, encoding='utf-8') as f:
        mock_submit.assert_called_with(f.read())


@mock.patch.object(coveralls.cli.log, 'warning')
@mock.patch.object(coveralls.Coveralls, 'submit_report')
@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_upload_deprecated_submit_warns(
    mock_submit: mock.MagicMock, mock_warning: mock.MagicMock,
) -> None:
    json_file = os.path.join(EXAMPLE_DIR, 'example.json')
    coveralls.cli.main(argv=['--submit=' + json_file])
    with open(json_file, encoding='utf-8') as f:
        mock_submit.assert_called_with(f.read())
    mock_warning.assert_called_once_with(
        '%s is deprecated and will be removed in a future release; use %s '
        'instead.', '--submit', 'coveralls upload FILE',
    )


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_deprecated_submit_applies_merge(
    mock_coveralls: mock.MagicMock,
) -> None:
    # The old flat CLI ran merge() before every action; the deprecated --submit
    # path must dispatch identically, so --merge is still applied.
    json_file = os.path.join(EXAMPLE_DIR, 'example.json')
    coveralls.cli.main(argv=['--submit=' + json_file, '--merge=extra.json'])
    mock_coveralls.return_value.merge.assert_called_once_with('extra.json')
    mock_coveralls.return_value.submit_report.assert_called_once()


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_upload_does_not_advertise_merge() -> None:
    with pytest.raises(SystemExit):
        coveralls.cli.main(argv=['upload', 'f', '--merge=extra.json'])
