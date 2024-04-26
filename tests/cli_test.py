import json
import os
from unittest import mock

import pytest
import responses

import coveralls.cli
from coveralls.exception import CoverallsException


EXC = CoverallsException('bad stuff happened')


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
EXAMPLE_DIR = os.path.join(BASE_DIR, 'example')


def req_json(request):
    return json.loads(request.body.decode('utf-8'))


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch.object(coveralls.cli.log, 'info')
@mock.patch.object(coveralls.Coveralls, 'wear')
def test_debug(mock_wear, mock_log):
    coveralls.cli.main(argv=['debug'])
    mock_wear.assert_called_with(dry_run=True)
    mock_log.assert_has_calls([mock.call('Testing coveralls-python...')])


@mock.patch.dict(os.environ, clear=True)
@mock.patch.object(coveralls.cli.log, 'info')
@mock.patch.object(coveralls.Coveralls, 'wear')
def test_debug_no_token(mock_wear, mock_log):
    coveralls.cli.main(argv=['debug'])
    mock_wear.assert_called_with(dry_run=True)
    mock_log.assert_has_calls([mock.call('Testing coveralls-python...')])


@mock.patch.dict(
    os.environ,
    {
        'GITHUB_ACTIONS': 'true',
        'GITHUB_REPOSITORY': 'test/repo',
        'GITHUB_TOKEN': 'xxx',
        'GITHUB_RUN_ID': '123456789',
        'GITHUB_RUN_NUMBER': '123',
    },
    clear=True,
)
@mock.patch.object(coveralls.cli.log, 'info')
@responses.activate
def test_finish(mock_log):
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

    coveralls.cli.main(argv=['--finish'])

    mock_log.assert_has_calls(
        [
            mock.call('Finishing parallel jobs...'),
            mock.call('Done'),
        ],
    )
    assert len(responses.calls) == 1
    assert req_json(responses.calls[0].request) == expected_json


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch.object(coveralls.cli.log, 'exception')
@responses.activate
def test_finish_exception(mock_log):
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

    with pytest.raises(SystemExit):
        coveralls.cli.main(argv=['--finish'])

    mock_log.assert_has_calls([
        mock.call(
            'Error running coveralls: %s',
            CoverallsException(msg),
        ),
    ])
    assert len(responses.calls) == 1
    assert req_json(responses.calls[0].request) == expected_json


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch.object(coveralls.cli.log, 'exception')
@responses.activate
def test_finish_exception_without_error(mock_log):
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

    with pytest.raises(SystemExit):
        coveralls.cli.main(argv=['--finish'])

    mock_log.assert_has_calls([
        mock.call(
            'Error running coveralls: %s',
            CoverallsException(msg),
        ),
    ])
    assert len(responses.calls) == 1
    assert req_json(responses.calls[0].request) == expected_json


@mock.patch.object(coveralls.cli.log, 'info')
@mock.patch.object(coveralls.Coveralls, 'wear')
@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_real(mock_wear, mock_log):
    coveralls.cli.main(argv=[])
    mock_wear.assert_called_with()
    mock_log.assert_has_calls(
        [
            mock.call('Submitting coverage to coveralls.io...'),
            mock.call('Coverage submitted!'),
        ],
    )


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_rcfile(mock_coveralls):
    coveralls.cli.main(argv=['--rcfile=coveragerc'])
    mock_coveralls.assert_called_with(
        True, config_file='coveragerc',
        service_name=None,
        base_dir='',
        src_dir='',
    )


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_service_name(mock_coveralls):
    coveralls.cli.main(argv=['--service=travis-pro'])
    mock_coveralls.assert_called_with(
        True, config_file='.coveragerc',
        service_name='travis-pro',
        base_dir='',
        src_dir='',
    )


@mock.patch.object(coveralls.cli.log, 'exception')
@mock.patch.object(coveralls.Coveralls, 'wear', side_effect=EXC)
@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_exception(_mock_coveralls, mock_log):
    with pytest.raises(SystemExit):
        coveralls.cli.main(argv=[])

    mock_log.assert_has_calls([mock.call('Error running coveralls: %s', EXC)])


@mock.patch.object(coveralls.Coveralls, 'save_report')
@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_save_report_to_file(mock_coveralls):
    """Check save_report api usage."""
    coveralls.cli.main(argv=['--output=test.log'])
    mock_coveralls.assert_called_with('test.log')


@mock.patch.dict(os.environ, clear=True)
@mock.patch.object(coveralls.Coveralls, 'save_report')
def test_save_report_to_file_no_token(mock_coveralls):
    """Check save_report api usage when token is not set."""
    coveralls.cli.main(argv=['--output=test.log'])
    mock_coveralls.assert_called_with('test.log')


@mock.patch.object(coveralls.Coveralls, 'submit_report')
@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_submit(mock_submit):
    json_file = os.path.join(EXAMPLE_DIR, 'example.json')
    coveralls.cli.main(argv=['--submit=' + json_file])
    with open(json_file) as f:
        mock_submit.assert_called_with(f.read())


@mock.patch('coveralls.cli.Coveralls')
def test_base_dir_arg(mock_coveralls):
    coveralls.cli.main(argv=['--basedir=foo'])
    mock_coveralls.assert_called_with(
        True, config_file='.coveragerc',
        service_name=None,
        base_dir='foo',
        src_dir='',
    )


@mock.patch('coveralls.cli.Coveralls')
def test_src_dir_arg(mock_coveralls):
    coveralls.cli.main(argv=['--srcdir=foo'])
    mock_coveralls.assert_called_with(
        True, config_file='.coveragerc',
        service_name=None,
        base_dir='',
        src_dir='foo',
    )
