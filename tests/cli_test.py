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


def coveralls_kwargs(**overrides):
    """Expected Coveralls() override kwargs: everything unset (None) initially.

    The CLI forwards every value as-is and lets resolve() drop the unset ones,
    so the constructor is always called with the full override set.

    Keep this in sync with the CLI option set: a new forwarded option must be
    added here, otherwise every test that uses the default set will silently
    under-assert on it.
    """
    kwargs = {
        'rcfile': None,
        'service_name': None,
        'base_dir': None,
        'src_dir': None,
        'host': None,
        'parallel': None,
        'skip_ssl_verify': None,
        'timeout': None,
        'connect_timeout': None,
        'read_timeout': None,
    }
    kwargs.update(overrides)
    return kwargs


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


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_debug_accepts_options(mock_coveralls):
    # the debug subcommand shares the full option set with the default command
    coveralls.cli.main(argv=['debug', '--rcfile=coveragerc', '--host=h'])
    mock_coveralls.assert_called_with(
        False, **coveralls_kwargs(rcfile='coveragerc', host='h'),
    )


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
        True, **coveralls_kwargs(rcfile='coveragerc'),
    )


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_service_name(mock_coveralls):
    coveralls.cli.main(argv=['--service-name=travis-pro'])
    mock_coveralls.assert_called_with(
        True, **coveralls_kwargs(service_name='travis-pro'),
    )


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_host_and_skip_ssl_verify_and_parallel(mock_coveralls):
    coveralls.cli.main(
        argv=[
            '--host=https://enterprise.example.com',
            '--skip-ssl-verify',
            '--parallel',
        ],
    )
    mock_coveralls.assert_called_with(
        True, **coveralls_kwargs(
            host='https://enterprise.example.com',
            parallel=True,
            skip_ssl_verify=True,
        ),
    )


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_no_parallel_and_no_skip_ssl_verify_forward_false(mock_coveralls):
    # --no-parallel / --no-skip-ssl-verify let the CLI express an explicit
    # False override (matching library callers), which resolve() applies over
    # an env/file value rather than being swallowed as an unset default.
    coveralls.cli.main(argv=['--no-parallel', '--no-skip-ssl-verify'])
    mock_coveralls.assert_called_with(
        True, **coveralls_kwargs(parallel=False, skip_ssl_verify=False),
    )


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch.object(coveralls.cli.log, 'warning')
@mock.patch('coveralls.cli.Coveralls')
def test_deprecated_service_alias_warns(mock_coveralls, mock_warning):
    coveralls.cli.main(argv=['--service=travis-pro'])
    mock_warning.assert_called_once_with(
        '%s is deprecated and will be removed in a future release; use %s '
        'instead.', '--service', '--service-name',
    )
    _, kwargs = mock_coveralls.call_args
    assert kwargs['service_name'] == 'travis-pro'


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
    coveralls.cli.main(argv=['--base-dir=foo'])
    mock_coveralls.assert_called_with(
        True, **coveralls_kwargs(base_dir='foo'),
    )


@mock.patch('coveralls.cli.Coveralls')
def test_src_dir_arg(mock_coveralls):
    coveralls.cli.main(argv=['--src-dir=foo'])
    mock_coveralls.assert_called_with(
        True, **coveralls_kwargs(src_dir='foo'),
    )


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_unset_timeout_args_are_none(mock_coveralls):
    # Unset options forward as None; resolve() drops them so nothing clobbers.
    coveralls.cli.main(argv=[])
    mock_coveralls.assert_called_with(True, **coveralls_kwargs())


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_timeout_arg(mock_coveralls):
    coveralls.cli.main(argv=['--timeout=30'])
    mock_coveralls.assert_called_with(True, **coveralls_kwargs(timeout=30.0))


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_connect_and_read_timeout_args(mock_coveralls):
    coveralls.cli.main(argv=['--connect-timeout=5', '--read-timeout=90'])
    mock_coveralls.assert_called_with(
        True, **coveralls_kwargs(connect_timeout=5.0, read_timeout=90.0),
    )
