import dataclasses

import pytest

from coveralls.configuration import Config
from coveralls.configuration import DEFAULT_CONNECT_TIMEOUT
from coveralls.configuration import DEFAULT_HOST
from coveralls.configuration import DEFAULT_READ_TIMEOUT
from coveralls.configuration import PAYLOAD_FIELDS
from coveralls.exception import CoverallsException


def test_defaults():
    config = Config()
    assert config.repo_token is None
    assert config.service_name == 'coveralls-python'
    assert config.parallel is None
    assert config.run_at is None
    assert config.coveralls_host == DEFAULT_HOST
    assert config.skip_ssl_verify is False
    assert config.token_required is True
    assert config.base_dir == ''
    assert config.src_dir == ''
    assert config.config_file is True
    assert config.timeout is None
    assert config.connect_timeout is None
    assert config.read_timeout is None


def test_to_payload_includes_only_set_payload_fields():
    config = Config(repo_token='xxx', service_name='travis-ci', parallel=True)
    assert config.to_payload() == {
        'repo_token': 'xxx',
        'service_name': 'travis-ci',
        'parallel': True,
    }


def test_to_payload_omits_unset_payload_fields():
    payload = Config(repo_token='xxx').to_payload()
    # service_name always defaults to a real value; everything else is unset
    assert payload == {'repo_token': 'xxx', 'service_name': 'coveralls-python'}
    # parallel is unset (None) here, so it is not advertised at all
    assert 'parallel' not in payload


def test_to_payload_forwards_explicitly_set_falsey_fields():
    # A caller who sets a payload field to a falsey value made an explicit
    # choice; it must be forwarded rather than dropped like an unset field.
    # parallel=False (an explicit --no-parallel) is the realistic falsey case.
    payload = Config(repo_token='xxx', parallel=False).to_payload()
    assert payload['parallel'] is False


# Keep in sync with Config: every field is either a PAYLOAD_FIELDS entry or
# listed here. test_payload_and_client_fields_..._cover_the_dataclass enforces
# this, so add new fields to one list or the other.
CLIENT_ONLY_FIELDS = (
    'coveralls_host',
    'skip_ssl_verify',
    'token_required',
    'base_dir',
    'src_dir',
    'config_file',
    'timeout',
    'connect_timeout',
    'read_timeout',
)


def test_client_settings_never_leak_into_payload():
    # Regression guard: base_dir/src_dir/config_file and the timeout family
    # have all historically leaked into the submitted JSON via a config bag.
    payload = Config(
        repo_token='xxx',
        coveralls_host='https://enterprise.example.com',
        skip_ssl_verify=True,
        base_dir='b',
        src_dir='s',
        config_file='.coveragerc',
        timeout=30,
        connect_timeout=5,
        read_timeout=25,
    ).to_payload()
    for name in CLIENT_ONLY_FIELDS:
        assert name not in payload


def test_payload_and_client_fields_are_disjoint_and_cover_the_dataclass():
    field_names = {f.name for f in dataclasses.fields(Config)}
    assert set(PAYLOAD_FIELDS).isdisjoint(CLIENT_ONLY_FIELDS)
    assert set(PAYLOAD_FIELDS) | set(CLIENT_ONLY_FIELDS) == field_names


TIMEOUT_FIELDS = ['timeout', 'connect_timeout', 'read_timeout']


@pytest.mark.parametrize('name', TIMEOUT_FIELDS)
def test_timeout_accepts_numeric_strings(name):
    config = Config(**{name: '15'})
    assert getattr(config, name) == 15.0


@pytest.mark.parametrize('name', TIMEOUT_FIELDS)
def test_timeout_rejects_non_numeric(name):
    with pytest.raises(CoverallsException, match='must be a number'):
        Config(**{name: 'abc'})


@pytest.mark.parametrize('name', TIMEOUT_FIELDS)
@pytest.mark.parametrize('value', [0, -1])
def test_timeout_rejects_non_positive(name, value):
    with pytest.raises(CoverallsException, match='greater than 0'):
        Config(**{name: value})


def test_request_timeout_defaults():
    assert Config().request_timeout == (
        DEFAULT_CONNECT_TIMEOUT, DEFAULT_READ_TIMEOUT,
    )


def test_request_timeout_overall_applies_to_both_phases():
    assert Config(timeout=30).request_timeout == (30.0, 30.0)


def test_request_timeout_phase_specific_wins_over_overall():
    config = Config(timeout=30, connect_timeout=5, read_timeout=45)
    assert config.request_timeout == (5.0, 45.0)


def test_request_timeout_phase_specific_falls_back_to_default():
    # only connect overridden -> read falls back to its default
    assert Config(connect_timeout=5).request_timeout == (
        5.0, DEFAULT_READ_TIMEOUT,
    )
