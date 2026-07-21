import json
import logging
import os
from typing import Any
from unittest import mock

import pytest
import responses

import coveralls.cli


EXC = RuntimeError('bad stuff happened')


BASE_DIR = os.path.dirname(os.path.dirname(__file__))
EXAMPLE_DIR = os.path.join(BASE_DIR, 'example')


def req_json(request: Any) -> Any:
    return json.loads(request.body.decode('utf-8'))


def assert_logged_error(
    caplog: pytest.LogCaptureFixture, msg: str,
) -> None:
    """Assert _run_action logged exactly one error carrying exception `msg`.

    _run_action logs via log.exception, so the failing exception is recorded
    in the record's exc_info rather than the message; we inspect that.
    """
    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errors) == 1
    record = errors[0]
    assert record.message == 'Error running coveralls'
    assert record.exc_info is not None
    assert str(record.exc_info[1]) == msg


def coveralls_kwargs(**overrides: Any) -> dict[str, Any]:
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
def test_debug(mock_wear: mock.MagicMock, mock_log: mock.MagicMock) -> None:
    coveralls.cli.main(argv=['debug'])
    mock_wear.assert_called_with(dry_run=True)
    mock_log.assert_has_calls([mock.call('Testing coveralls-python...')])


@mock.patch.dict(os.environ, clear=True)
@mock.patch.object(coveralls.cli.log, 'info')
@mock.patch.object(coveralls.Coveralls, 'wear')
def test_debug_no_token(
    mock_wear: mock.MagicMock, mock_log: mock.MagicMock,
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
        False, **coveralls_kwargs(rcfile='coveragerc', host='h'),
    )


def _github_finish_env() -> dict[str, str]:
    return {
        'GITHUB_ACTIONS': 'true',
        'GITHUB_REPOSITORY': 'test/repo',
        'GITHUB_TOKEN': 'xxx',
        'GITHUB_RUN_ID': '123456789',
        'GITHUB_RUN_NUMBER': '123',
    }


@mock.patch.dict(os.environ, _github_finish_env(), clear=True)
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


@mock.patch.dict(os.environ, _github_finish_env(), clear=True)
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


@mock.patch.object(coveralls.cli.log, 'info')
@mock.patch.object(coveralls.Coveralls, 'wear')
@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_real(mock_wear: mock.MagicMock, mock_log: mock.MagicMock) -> None:
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
def test_rcfile(mock_coveralls: mock.MagicMock) -> None:
    coveralls.cli.main(argv=['--rcfile=coveragerc'])
    mock_coveralls.assert_called_with(
        True, **coveralls_kwargs(rcfile='coveragerc'),
    )


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_service_name(mock_coveralls: mock.MagicMock) -> None:
    coveralls.cli.main(argv=['--service-name=travis-pro'])
    mock_coveralls.assert_called_with(
        True, **coveralls_kwargs(service_name='travis-pro'),
    )


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_host_and_skip_ssl_verify_and_parallel(
    mock_coveralls: mock.MagicMock,
) -> None:
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
def test_no_parallel_and_no_skip_ssl_verify_forward_false(
    mock_coveralls: mock.MagicMock,
) -> None:
    # --no-parallel / --no-skip-ssl-verify let the CLI express an explicit
    # False override (matching library callers), which resolve() applies over
    # an env/file value rather than being swallowed as an unset default.
    coveralls.cli.main(argv=['--no-parallel', '--no-skip-ssl-verify'])
    mock_coveralls.assert_called_with(
        True, **coveralls_kwargs(parallel=False, skip_ssl_verify=False),
    )


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_merge_before_submit(mock_coveralls: mock.MagicMock) -> None:
    # --merge folds an extra report into the data before the default submit.
    coveralls.cli.main(argv=['--merge=extra.json'])
    mock_coveralls.return_value.merge.assert_called_once_with('extra.json')
    mock_coveralls.return_value.wear.assert_called_once_with()


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch.object(coveralls.cli.log, 'warning')
@mock.patch('coveralls.cli.Coveralls')
def test_deprecated_service_alias_warns(
    mock_coveralls: mock.MagicMock, mock_warning: mock.MagicMock,
) -> None:
    coveralls.cli.main(argv=['--service=travis-pro'])
    mock_warning.assert_called_once_with(
        '%s is deprecated and will be removed in a future release; use %s '
        'instead.', '--service', '--service-name',
    )
    _, kwargs = mock_coveralls.call_args
    assert kwargs['service_name'] == 'travis-pro'


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch.object(coveralls.cli.log, 'warning')
@mock.patch('coveralls.cli.Coveralls')
def test_deprecated_basedir_alias_warns(
    mock_coveralls: mock.MagicMock, mock_warning: mock.MagicMock,
) -> None:
    coveralls.cli.main(argv=['--basedir=foo'])
    mock_warning.assert_called_once_with(
        '%s is deprecated and will be removed in a future release; use %s '
        'instead.', '--basedir', '--base-dir',
    )
    _, kwargs = mock_coveralls.call_args
    assert kwargs['base_dir'] == 'foo'


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch.object(coveralls.cli.log, 'warning')
@mock.patch('coveralls.cli.Coveralls')
def test_deprecated_srcdir_alias_warns(
    mock_coveralls: mock.MagicMock, mock_warning: mock.MagicMock,
) -> None:
    coveralls.cli.main(argv=['--srcdir=foo'])
    mock_warning.assert_called_once_with(
        '%s is deprecated and will be removed in a future release; use %s '
        'instead.', '--srcdir', '--src-dir',
    )
    _, kwargs = mock_coveralls.call_args
    assert kwargs['src_dir'] == 'foo'


@mock.patch.object(coveralls.Coveralls, 'wear', side_effect=EXC)
@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_exception(
    _mock_coveralls: mock.MagicMock, caplog: pytest.LogCaptureFixture,
) -> None:
    with pytest.raises(SystemExit), caplog.at_level(logging.ERROR):
        coveralls.cli.main(argv=[])

    errors = [r for r in caplog.records if r.levelno == logging.ERROR]
    assert len(errors) == 1
    assert errors[0].message == 'Error running coveralls'
    assert errors[0].exc_info is not None
    assert errors[0].exc_info[1] is EXC


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
    mock_save: mock.MagicMock, mock_warning: mock.MagicMock,
) -> None:
    coveralls.cli.main(argv=['--output=test.log'])
    mock_save.assert_called_with('test.log')
    mock_warning.assert_called_once_with(
        '%s is deprecated and will be removed in a future release; use %s '
        'instead.', '--output', 'coveralls save FILE',
    )


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
@mock.patch('coveralls.cli.Coveralls')
def test_deprecated_finish_applies_merge(
    mock_coveralls: mock.MagicMock,
) -> None:
    coveralls.cli.main(argv=['--finish', '--merge=extra.json'])
    mock_coveralls.return_value.merge.assert_called_once_with('extra.json')
    mock_coveralls.return_value.parallel_finish.assert_called_once_with()


@mock.patch('coveralls.cli.Coveralls')
def test_base_dir_arg(mock_coveralls: mock.MagicMock) -> None:
    coveralls.cli.main(argv=['--base-dir=foo'])
    mock_coveralls.assert_called_with(
        True, **coveralls_kwargs(base_dir='foo'),
    )


@mock.patch('coveralls.cli.Coveralls')
def test_src_dir_arg(mock_coveralls: mock.MagicMock) -> None:
    coveralls.cli.main(argv=['--src-dir=foo'])
    mock_coveralls.assert_called_with(
        True, **coveralls_kwargs(src_dir='foo'),
    )


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_unset_timeout_args_are_none(mock_coveralls: mock.MagicMock) -> None:
    # Unset options forward as None; resolve() drops them so nothing clobbers.
    coveralls.cli.main(argv=[])
    mock_coveralls.assert_called_with(True, **coveralls_kwargs())


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_timeout_arg(mock_coveralls: mock.MagicMock) -> None:
    coveralls.cli.main(argv=['--timeout=30'])
    mock_coveralls.assert_called_with(True, **coveralls_kwargs(timeout=30.0))


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_connect_and_read_timeout_args(mock_coveralls: mock.MagicMock) -> None:
    coveralls.cli.main(argv=['--connect-timeout=5', '--read-timeout=90'])
    mock_coveralls.assert_called_with(
        True, **coveralls_kwargs(connect_timeout=5.0, read_timeout=90.0),
    )


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
@mock.patch('coveralls.cli.Coveralls')
def test_submit_family_accepts_merge_and_parallel(
    mock_coveralls: mock.MagicMock,
) -> None:
    # save/debug build a report, so they honour the submit-only modifiers.
    coveralls.cli.main(argv=['save', 'o', '--parallel', '--merge=extra.json'])
    mock_coveralls.assert_called_with(
        False, **coveralls_kwargs(parallel=True),
    )
    mock_coveralls.return_value.merge.assert_called_once_with('extra.json')
    mock_coveralls.return_value.save_report.assert_called_once_with('o')


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_deprecated_verb_flag_with_subcommand_errors() -> None:
    with pytest.raises(SystemExit):
        coveralls.cli.main(argv=['--finish', 'save', 'o'])


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_multiple_deprecated_verb_flags_error() -> None:
    with pytest.raises(SystemExit):
        coveralls.cli.main(argv=['--output=a', '--submit=b'])


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_debug_does_not_advertise_verbose() -> None:
    # debug always forces verbose, so it does not offer a redundant --verbose.
    with pytest.raises(SystemExit):
        coveralls.cli.main(argv=['debug', '--verbose'])


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_finish_does_not_advertise_parallel() -> None:
    # finish ignores report-building modifiers, so it does not accept them.
    with pytest.raises(SystemExit):
        coveralls.cli.main(argv=['finish', '--parallel'])


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_upload_does_not_advertise_merge() -> None:
    with pytest.raises(SystemExit):
        coveralls.cli.main(argv=['upload', 'f', '--merge=extra.json'])
