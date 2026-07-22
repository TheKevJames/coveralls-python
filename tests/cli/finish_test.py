import logging
import os
from unittest import mock

import pytest
import responses

import coveralls.cli
from tests.cli.conftest import assert_logged_error
from tests.cli.conftest import github_finish_env
from tests.cli.conftest import req_json


@mock.patch.dict(os.environ, github_finish_env(), clear=True)
@mock.patch.object(coveralls.cli.log, 'info')
@responses.activate
def test_finish(mock_log: mock.MagicMock) -> None:
    responses.add(
        responses.POST, 'https://coveralls.io/webhook',
        json={'done': True}, status=200,
    )
    expected_json = {
        'repo_token': 'xxx',
        'repo_name': 'test/repo',
        'payload': {
            'status': 'done',
            'build_num': '123456789',
        },
    }

    coveralls.cli.main(argv=['finish'])

    mock_log.assert_has_calls(
        [
            mock.call('Finishing parallel jobs...'),
            mock.call('Done'),
        ],
    )
    assert len(responses.calls) == 1
    assert req_json(responses.calls[0].request) == expected_json


@mock.patch.dict(os.environ, github_finish_env(), clear=True)
@responses.activate
def test_finish_carryforward_in_webhook_payload() -> None:
    responses.add(
        responses.POST, 'https://coveralls.io/webhook',
        json={'done': True}, status=200,
    )

    coveralls.cli.main(argv=['finish', '--carryforward=flag1,flag2'])

    assert len(responses.calls) == 1
    body = req_json(responses.calls[0].request)
    assert body['carryforward'] == 'flag1,flag2'


@mock.patch.dict(os.environ, github_finish_env(), clear=True)
@mock.patch.object(coveralls.cli.log, 'warning')
@responses.activate
def test_finish_deprecated_flag_warns(mock_warning: mock.MagicMock) -> None:
    responses.add(
        responses.POST, 'https://coveralls.io/webhook',
        json={'done': True}, status=200,
    )

    coveralls.cli.main(argv=['--finish'])

    mock_warning.assert_called_once_with(
        '%s is deprecated and will be removed in a future release; use %s '
        'instead.', '--finish', 'coveralls finish',
    )
    assert len(responses.calls) == 1


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@responses.activate
def test_finish_exception(caplog: pytest.LogCaptureFixture) -> None:
    responses.add(
        responses.POST, 'https://coveralls.io/webhook',
        json={'error': 'Mocked'}, status=200,
    )
    expected_json = {
        'payload': {
            'status': 'done',
        },
    }
    msg = 'Parallel finish failed: Mocked'

    with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
        coveralls.cli.main(argv=['finish'])

    assert_logged_error(caplog, msg)
    assert len(responses.calls) == 1
    assert req_json(responses.calls[0].request) == expected_json


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@responses.activate
def test_finish_exception_without_error(
    caplog: pytest.LogCaptureFixture,
) -> None:
    responses.add(
        responses.POST, 'https://coveralls.io/webhook',
        json={}, status=200,
    )
    expected_json = {
        'payload': {
            'status': 'done',
        },
    }
    msg = 'Parallel finish failed'

    with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
        coveralls.cli.main(argv=['finish'])

    assert_logged_error(caplog, msg)
    assert len(responses.calls) == 1
    assert req_json(responses.calls[0].request) == expected_json


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_deprecated_finish_applies_merge(
    mock_coveralls: mock.MagicMock,
) -> None:
    coveralls.cli.main(argv=['--finish', '--merge=extra.json'])
    mock_coveralls.return_value.merge.assert_called_once_with('extra.json')
    mock_coveralls.return_value.parallel_finish.assert_called_once_with()


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_finish_does_not_advertise_parallel() -> None:
    # finish ignores report-building modifiers, so it does not accept them.
    with pytest.raises(SystemExit):
        coveralls.cli.main(argv=['finish', '--parallel'])
