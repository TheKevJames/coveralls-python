import logging
import os
from unittest import mock

import pytest

import coveralls.cli
from tests.cli.conftest import coveralls_kwargs
from tests.cli.conftest import EXC


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
def test_deprecated_verb_flag_with_subcommand_errors() -> None:
    with pytest.raises(SystemExit):
        coveralls.cli.main(argv=['--finish', 'save', 'o'])


@mock.patch.dict(os.environ, {'TRAVIS': 'True'}, clear=True)
def test_multiple_deprecated_verb_flags_error() -> None:
    with pytest.raises(SystemExit):
        coveralls.cli.main(argv=['--output=a', '--submit=b'])
