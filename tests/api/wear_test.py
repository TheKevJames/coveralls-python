import contextlib
import json
import os
import pathlib
import socket
import tempfile
import threading
import unittest.mock
from collections.abc import Iterator
from typing import Any

import coverage
import pytest
import requests
import responses
from requests.adapters import HTTPAdapter

import coveralls
from coveralls.api import RETRY_BACKOFF_MAX
from coveralls.api import _build_session
from coveralls.api import log

EXPECTED = {
    'message': 'Job #7.1 - 44.58% Covered',
    'url': 'https://coveralls.io/jobs/5869',
}
JOBS_URL = 'https://coveralls.io/api/v1/jobs'
WEBHOOK_URL = 'https://coveralls.io/webhook'


def req_kwargs(call: Any) -> Any:
    # responses attaches the send() kwargs (timeout, verify, ...) to the
    # captured request; they are not part of the typed PreparedRequest API.
    return call.request.req_kwargs


def req_json(call: Any) -> Any:
    return json.loads(call.request.body)


@pytest.fixture(autouse=True)
def _no_coverage_file() -> None:
    with contextlib.suppress(Exception):
        pathlib.Path('.coverage').unlink()


@pytest.fixture(autouse=True)
def _no_backoff_sleep() -> Iterator[None]:
    # urllib3's Retry sleeps between attempts; stub it so the retry tests stay
    # instant regardless of the configured backoff strategy.
    with unittest.mock.patch('urllib3.util.retry.time.sleep'):
        yield


@responses.activate
def test_wet_run() -> None:
    responses.add(responses.POST, JOBS_URL, json=EXPECTED, status=200)
    result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)
    assert result == EXPECTED


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_client_settings_do_not_leak_into_payload() -> None:
    # Regression guard at the create_data() boundary: base_dir/src_dir/rcfile
    # and the timeout/retries families are client-only and must never enter
    # the submitted JSON.
    api = coveralls.Coveralls(
        repo_token='xxx',
        service_name='travis-ci',
        base_dir='foo',
        src_dir='bar',
        rcfile='.coveragerc',
        timeout=30,
        connect_timeout=5,
        read_timeout=25,
        retries=3,
    )
    with unittest.mock.patch.object(api, 'get_coverage', return_value=[]):
        data = api.create_data()

    for leaked in (
        'base_dir',
        'src_dir',
        'rcfile',
        'config_file',
        'timeout',
        'connect_timeout',
        'read_timeout',
        'retries',
    ):
        assert leaked not in data
    assert data['repo_token'] == 'xxx'
    assert data['service_name'] == 'travis-ci'


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_set_payload_fields_are_forwarded_including_falsey() -> None:
    # Every job field the API accepts is forwarded when set -- including
    # run_at, and including explicitly-falsey values (parallel=False, a
    # numeric 0 job id). Only genuinely-absent fields are dropped.
    api = coveralls.Coveralls(
        repo_token='xxx',
        service_name='travis-ci',
        run_at='2013-02-18 00:52:48 -0800',
        parallel=False,
        service_job_id=0,
    )
    with unittest.mock.patch.object(api, 'get_coverage', return_value=[]):
        data = api.create_data()

    assert data['run_at'] == '2013-02-18 00:52:48 -0800'
    assert data['parallel'] is False
    assert data['service_job_id'] == 0


def test_merge() -> None:
    with tempfile.NamedTemporaryFile() as coverage_file:
        coverage_file.write(
            b'{"source_files": [{"name": "foobar", "coverage": []}]}'
        )
        coverage_file.seek(0)

        api = coveralls.Coveralls(repo_token='xxx')
        api.merge(coverage_file.name)
        result = api.create_report()

        source_files = json.loads(result)['source_files']
        assert source_files == [{'name': 'foobar', 'coverage': []}]


def test_merge_empty_data() -> None:
    with tempfile.NamedTemporaryFile() as coverage_file:
        coverage_file.write(b'{}')
        coverage_file.seek(0)

        api = coveralls.Coveralls(repo_token='xxx')
        api.merge(coverage_file.name)
        result = api.create_report()

        source_files = json.loads(result)['source_files']
        assert source_files == []


def test_merge_invalid_data() -> None:
    with tempfile.NamedTemporaryFile() as coverage_file:
        coverage_file.write(b'{"random": "stuff"}')
        coverage_file.seek(0)

        with unittest.mock.patch.object(log, 'warning') as logger:
            api = coveralls.Coveralls(repo_token='xxx')
            api.merge(coverage_file.name)
            result = api.create_report()

        source_files = json.loads(result)['source_files']
        assert source_files == []

        logger.assert_called_once_with(
            'No data to be merged; does the json file contain '
            '"source_files" data?'
        )


@responses.activate
def test_dry_run() -> None:
    result = coveralls.Coveralls(repo_token='xxx').wear(dry_run=True)
    assert not result
    assert not responses.calls


@responses.activate
def test_repo_token_in_not_compromised_verbose() -> None:
    with unittest.mock.patch.object(log, 'debug') as logger:
        coveralls.Coveralls(repo_token='xxx').wear(dry_run=True)

    assert 'xxx' not in logger.call_args[0][0]


@responses.activate
def test_coveralls_unavailable() -> None:
    responses.add(
        responses.POST, JOBS_URL, body='<html>Http 1./1 500</html>', status=500
    )
    with pytest.raises(RuntimeError):
        coveralls.Coveralls(repo_token='xxx').wear()
    assert len(responses.calls) == 1


@responses.activate
@unittest.mock.patch('coveralls.reporter.CoverallReporter.report')
def test_no_coverage(report_files: unittest.mock.MagicMock) -> None:
    report_files.side_effect = coverage.CoverageException('No data to report')
    with pytest.raises(coverage.CoverageException):
        coveralls.Coveralls(repo_token='xxx').wear()


@unittest.mock.patch.dict(
    os.environ,
    {
        'COVERALLS_HOST': 'https://coveralls.my-enterprise.info',
        'COVERALLS_SKIP_SSL_VERIFY': '1',
    },
    clear=True,
)
@responses.activate
def test_coveralls_host_env_var_overrides_api_url() -> None:
    endpoint = 'https://coveralls.my-enterprise.info/api/v1/jobs'
    responses.add(responses.POST, endpoint, json=EXPECTED, status=200)
    coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == endpoint
    assert req_kwargs(responses.calls[0])['verify'] is False
    assert req_kwargs(responses.calls[0])['timeout'] == (10, 60)


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_host_and_skip_ssl_verify_via_override() -> None:
    # host/skip_ssl_verify are first-class Config fields, settable through any
    # channel -- here as explicit overrides, not just env vars.
    endpoint = 'https://coveralls.my-enterprise.info/api/v1/jobs'
    responses.add(responses.POST, endpoint, json=EXPECTED, status=200)
    coveralls.Coveralls(
        repo_token='xxx',
        host='https://coveralls.my-enterprise.info',
        skip_ssl_verify=True,
    ).wear(dry_run=False)

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == endpoint
    assert req_kwargs(responses.calls[0])['verify'] is False


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_api_call_uses_default_host_if_no_env_var_set() -> None:
    responses.add(responses.POST, JOBS_URL, json=EXPECTED, status=200)
    coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == JOBS_URL
    assert req_kwargs(responses.calls[0])['verify'] is True
    assert req_kwargs(responses.calls[0])['timeout'] == (10, 60)


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_submit_report_uses_default_timeout() -> None:
    responses.add(responses.POST, JOBS_URL, json=EXPECTED, status=200)
    coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)
    assert req_kwargs(responses.calls[0])['timeout'] == (10, 60)


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_submit_report_raises_on_timeout() -> None:
    responses.add(
        responses.POST,
        JOBS_URL,
        body=requests.exceptions.ConnectTimeout('boom'),
    )
    with pytest.raises(TimeoutError, match=r'Request timeout'):
        coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)


@contextlib.contextmanager
def _hanging_server() -> Iterator[str]:
    # A server that accepts connections in the background but never responds,
    # so connects succeed and every request hits a read timeout. responses
    # cannot exercise this: it short-circuits urllib3's transport, and an
    # injected ReadTimeout does not reproduce urllib3's read=0/False remapping
    # nor the ConnectionError-wrapped MaxRetryError from exhausted retries.
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('127.0.0.1', 0))
    server.listen(5)
    held: list[socket.socket] = []
    stop = threading.Event()

    def accept_loop() -> None:
        server.settimeout(0.1)
        while not stop.is_set():
            with contextlib.suppress(OSError):
                conn, _ = server.accept()
                held.append(conn)

    thread = threading.Thread(target=accept_loop, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.getsockname()[1]}'
    finally:
        stop.set()
        thread.join(timeout=1)
        for conn in held:
            conn.close()
        server.close()


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_submit_report_read_timeout_raises_timeout_error() -> None:
    # Regression guard: with retries off (the default) a read timeout must
    # still surface as TimeoutError, not the generic "Could not submit
    # coverage" RuntimeError. See _build_session's read=0/False handling.
    with _hanging_server() as host:
        api = coveralls.Coveralls(
            repo_token='xxx', host=host, connect_timeout=5, read_timeout=0.5
        )
        with pytest.raises(TimeoutError, match=r'Request timeout'):
            api.wear(dry_run=False)


@unittest.mock.patch.dict(os.environ, {}, clear=True)
def test_submit_report_exhausted_read_timeout_raises_timeout_error() -> None:
    # With retries on, an exhausted read timeout surfaces from requests as a
    # ConnectionError wrapping a urllib3 timeout; it must still be reported as
    # the detailed TimeoutError, not the generic RuntimeError.
    with _hanging_server() as host:
        api = coveralls.Coveralls(
            repo_token='xxx',
            host=host,
            connect_timeout=5,
            read_timeout=0.3,
            retries=2,
        )
        with pytest.raises(TimeoutError, match=r'Request timeout'):
            api.wear(dry_run=False)


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_parallel_finish_uses_default_timeout() -> None:
    responses.add(responses.POST, WEBHOOK_URL, json={'done': True}, status=200)
    coveralls.Coveralls(repo_token='xxx').parallel_finish()
    assert req_kwargs(responses.calls[0])['timeout'] == (10, 60)


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_parallel_finish_sends_carryforward() -> None:
    responses.add(responses.POST, WEBHOOK_URL, json={'done': True}, status=200)
    coveralls.Coveralls(repo_token='xxx', carryforward='a,b').parallel_finish()
    assert req_json(responses.calls[0])['carryforward'] == 'a,b'


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_parallel_finish_omits_unset_carryforward() -> None:
    responses.add(responses.POST, WEBHOOK_URL, json={'done': True}, status=200)
    coveralls.Coveralls(repo_token='xxx').parallel_finish()
    assert 'carryforward' not in req_json(responses.calls[0])


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_parallel_finish_raises_on_timeout() -> None:
    responses.add(
        responses.POST,
        WEBHOOK_URL,
        body=requests.exceptions.ConnectTimeout('boom'),
    )
    with pytest.raises(TimeoutError, match=r'Request timeout'):
        coveralls.Coveralls(repo_token='xxx').parallel_finish()


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_submit_report_retries_transient_then_succeeds() -> None:
    responses.add(responses.POST, JOBS_URL, json={'e': 1}, status=502)
    responses.add(responses.POST, JOBS_URL, json={'e': 1}, status=503)
    responses.add(responses.POST, JOBS_URL, json=EXPECTED, status=200)

    result = coveralls.Coveralls(repo_token='xxx', retries=2).wear(
        dry_run=False
    )

    assert result == EXPECTED
    assert len(responses.calls) == 3


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_submit_report_retries_exhausted_raises() -> None:
    for _ in range(5):
        responses.add(responses.POST, JOBS_URL, json={'e': 1}, status=500)

    with pytest.raises(RuntimeError):
        coveralls.Coveralls(repo_token='xxx', retries=2).wear(dry_run=False)

    # one initial attempt plus two retries
    assert len(responses.calls) == 3


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_submit_report_retries_on_429() -> None:
    responses.add(responses.POST, JOBS_URL, json={'e': 1}, status=429)
    responses.add(responses.POST, JOBS_URL, json=EXPECTED, status=200)

    result = coveralls.Coveralls(repo_token='xxx', retries=1).wear(
        dry_run=False
    )

    assert result == EXPECTED
    assert len(responses.calls) == 2


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_submit_report_does_not_retry_422() -> None:
    # A 422 is a client/configuration error, never a transient failure: it
    # must not be retried even when retries are configured.
    for _ in range(5):
        responses.add(responses.POST, JOBS_URL, json={'e': 1}, status=422)

    with pytest.raises(RuntimeError):
        coveralls.Coveralls(repo_token='xxx', retries=3).wear(dry_run=False)

    assert len(responses.calls) == 1


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_submit_report_defaults_to_no_retries() -> None:
    # Regression guard: with no retries configured a single attempt is made,
    # preserving the historical behaviour.
    for _ in range(5):
        responses.add(responses.POST, JOBS_URL, json={'e': 1}, status=500)

    with pytest.raises(RuntimeError):
        coveralls.Coveralls(repo_token='xxx').wear(dry_run=False)

    assert len(responses.calls) == 1


def test_retries_do_not_honour_retry_after_header() -> None:
    # A server can send an arbitrarily large Retry-After (e.g. 3600s); urllib3
    # only began clamping it -- to 6 hours -- in 2.6.3, so honouring it could
    # hang CI for hours on our supported range. Guard that we ignore the header
    # and rely on our own bounded backoff instead. This cannot be exercised via
    # responses, which does not drive urllib3's retry sleep machinery.
    adapter = _build_session(3).get_adapter('https://coveralls.io')
    assert isinstance(adapter, HTTPAdapter)
    retry = adapter.max_retries
    assert retry.respect_retry_after_header is False
    assert retry.backoff_max == RETRY_BACKOFF_MAX


@unittest.mock.patch.dict(os.environ, {}, clear=True)
@responses.activate
def test_parallel_finish_retries_transient_then_succeeds() -> None:
    responses.add(responses.POST, WEBHOOK_URL, json={'e': 1}, status=503)
    responses.add(responses.POST, WEBHOOK_URL, json={'done': True}, status=200)

    coveralls.Coveralls(repo_token='xxx', retries=1).parallel_finish()

    assert len(responses.calls) == 2
