import dataclasses
from typing import Any

import pytest

from coveralls.configuration import Config
from coveralls.configuration.ci import _parse_pr_number
from coveralls.configuration.helpers import DEFAULT_CONNECT_TIMEOUT
from coveralls.configuration.helpers import DEFAULT_HOST
from coveralls.configuration.helpers import DEFAULT_READ_TIMEOUT
from coveralls.configuration.helpers import PAYLOAD_FIELDS


def test_defaults() -> None:
    config = Config()
    assert config.repo_token is None
    assert config.service_name == 'coveralls-python'
    assert config.parallel is None
    assert config.run_at is None
    assert config.host == DEFAULT_HOST
    assert not config.skip_ssl_verify
    assert config.token_required
    assert config.base_dir == ''
    assert config.src_dir == ''
    assert config.rcfile is True
    assert config.timeout is None
    assert config.connect_timeout is None
    assert config.read_timeout is None
    assert config.retries == 0


def test_to_payload_includes_only_set_payload_fields() -> None:
    config = Config(repo_token='xxx', service_name='travis-ci', parallel=True)
    assert config.to_payload() == {
        'repo_token': 'xxx',
        'service_name': 'travis-ci',
        'parallel': True,
    }


def test_to_payload_omits_unset_payload_fields() -> None:
    payload = Config(repo_token='xxx').to_payload()
    # service_name always defaults to a real value; everything else is unset
    assert payload == {'repo_token': 'xxx', 'service_name': 'coveralls-python'}
    # parallel is unset (None) here, so it is not advertised at all
    assert 'parallel' not in payload


def test_to_payload_forwards_explicitly_set_falsey_fields() -> None:
    # A caller who sets a payload field to a falsey value made an explicit
    # choice; it must be forwarded rather than dropped like an unset field.
    # parallel=False (an explicit --no-parallel) is the realistic falsey case.
    payload = Config(repo_token='xxx', parallel=False).to_payload()
    assert payload['parallel'] is False


# Keep in sync with Config: every field is either a PAYLOAD_FIELDS entry or
# listed here. test_payload_and_client_fields_..._cover_the_dataclass enforces
# this, so add new fields to one list or the other.
CLIENT_ONLY_FIELDS = (
    'carryforward',
    'host',
    'skip_ssl_verify',
    'token_required',
    'base_dir',
    'src_dir',
    'rcfile',
    'timeout',
    'connect_timeout',
    'read_timeout',
    'retries',
)


def test_client_settings_never_leak_into_payload() -> None:
    # Regression guard: base_dir/src_dir/rcfile and the timeout family have all
    # historically leaked into the submitted JSON via an untyped config bag.
    payload = Config(
        repo_token='xxx',
        host='https://enterprise.example.com',
        skip_ssl_verify=True,
        base_dir='b',
        src_dir='s',
        rcfile='.coveragerc',
        timeout=30,
        connect_timeout=5,
        read_timeout=25,
        retries=3,
    ).to_payload()
    for name in CLIENT_ONLY_FIELDS:
        assert name not in payload


def test_payload_and_client_fields_are_disjoint_and_cover_the_dataclass(
) -> None:
    field_names = {f.name for f in dataclasses.fields(Config)}
    assert set(PAYLOAD_FIELDS).isdisjoint(CLIENT_ONLY_FIELDS)
    assert set(PAYLOAD_FIELDS) | set(CLIENT_ONLY_FIELDS) == field_names


TIMEOUT_FIELDS = ['timeout', 'connect_timeout', 'read_timeout']


@pytest.mark.parametrize('name', TIMEOUT_FIELDS)
def test_timeout_accepts_numeric_strings(name: str) -> None:
    kwargs: dict[str, Any] = {name: '15'}
    config = Config(**kwargs)
    assert getattr(config, name) == 15.0


@pytest.mark.parametrize('name', TIMEOUT_FIELDS)
def test_timeout_rejects_non_numeric(name: str) -> None:
    kwargs: dict[str, Any] = {name: 'abc'}
    with pytest.raises(ValueError, match='must be a number'):
        Config(**kwargs)


@pytest.mark.parametrize('name', TIMEOUT_FIELDS)
@pytest.mark.parametrize('value', [0, -1])
def test_timeout_rejects_non_positive(name: str, value: int) -> None:
    kwargs: dict[str, Any] = {name: value}
    with pytest.raises(ValueError, match='greater than 0'):
        Config(**kwargs)


def test_request_timeout_defaults() -> None:
    assert Config().request_timeout == (
        DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT,
    )


def test_request_timeout_overall_applies_to_both_phases() -> None:
    assert Config(timeout=30).request_timeout == (30.0, 30.0)


def test_request_timeout_phase_specific_wins_over_overall() -> None:
    config = Config(timeout=30, connect_timeout=5, read_timeout=45)
    assert config.request_timeout == (5.0, 45.0)


def test_request_timeout_phase_specific_falls_back_to_default() -> None:
    # only connect overridden -> read falls back to its default
    assert Config(connect_timeout=5).request_timeout == (
        5.0, DEFAULT_READ_TIMEOUT,
    )


def test_retries_defaults_to_zero() -> None:
    assert Config().retries == 0


@pytest.mark.parametrize(('raw', 'expected'), [(0, 0), (3, 3), ('5', 5)])
def test_retries_accepts_non_negative_integers(
    raw: Any, expected: int,
) -> None:
    assert Config(retries=raw).retries == expected


@pytest.mark.parametrize('raw', ['abc', '1.5', '2.0', 2.5, 2.0, True, False])
def test_retries_rejects_non_integers(raw: Any) -> None:
    with pytest.raises(ValueError, match='must be an integer'):
        Config(retries=raw)


def test_retries_rejects_negative() -> None:
    with pytest.raises(ValueError, match='must not be negative'):
        Config(retries=-1)


@pytest.mark.parametrize(
    ('value', 'expected'),
    [
        ('42', '42'),
        ('pull/42', '42'),
        ('https://github.com/org/repo/pull/42', '42'),
        ('', None),
        (None, None),
        ('pull/42/', None),
    ],
)
def test_parse_pr_number(value: str | None, expected: str | None) -> None:
    # All CI loaders share this one trailing-integer semantic.
    assert _parse_pr_number(value) == expected
