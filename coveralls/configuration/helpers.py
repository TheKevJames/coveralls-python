import dataclasses
import datetime
import logging
import os
from collections.abc import Mapping
from typing import Any

log = logging.getLogger('coveralls.configuration.helpers')

# The config file sources coveralls-python reads. See files._from_files for
# the search/precedence rules.
YAML_CONFIG_FILE = '.coveralls.yml'
TOML_CONFIG_FILE = 'pyproject.toml'

DEFAULT_HOST = 'https://coveralls.io/'

# Used when no CI service is detected and none is configured explicitly.
DEFAULT_SERVICE_NAME = 'coveralls-python'

# requests has no wall-clock "total" timeout: a scalar applies separately to
# the connect and read phases. We always resolve an explicit (connect, read)
# tuple so a stalled endpoint can never hang the CLI indefinitely.
DEFAULT_CONNECT_TIMEOUT = 10
DEFAULT_READ_TIMEOUT = 60

DEFAULT_RETRIES = 0


def default_run_at() -> str:
    """Current local time as an RFC 3339 timestamp, e.g. the /jobs run_at."""
    return (
        datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
    )


# Fields sent to the coveralls.io API -- every job parameter the /jobs endpoint
# accepts and lets the caller set. Everything else on Config controls local
# client behaviour and must never enter the submitted payload.
# See https://docs.coveralls.io/api-jobs-endpoint (service_build_url and
# service_branch are not in that table but are populated from CI and accepted;
# git and source_files are computed elsewhere, not sourced from config).
PAYLOAD_FIELDS = (
    'repo_token',
    'service_name',
    'service_number',
    'service_job_id',
    'service_job_number',
    'service_pull_request',
    'service_branch',
    'service_build_url',
    'flag_name',
    'parallel',
    'run_at',
)


@dataclasses.dataclass
class Config:
    # pylint: disable=too-many-instance-attributes
    """
    Fully resolved coveralls-python configuration.

    Fields fall into two groups. The :data:`PAYLOAD_FIELDS` are sent to the
    coveralls.io API via :meth:`to_payload`; every other field controls local
    client behaviour (where to send, how to talk to coverage.py, etc.) and is
    deliberately never included in the submitted payload.
    """

    # payload fields
    repo_token: str | None = None
    service_name: str = DEFAULT_SERVICE_NAME
    service_number: str | None = None
    service_job_id: str | None = None
    service_job_number: str | None = None
    service_pull_request: str | None = None
    service_branch: str | None = None
    service_build_url: str | None = None
    flag_name: str | None = None
    # None means "unset"; an explicit True/False is forwarded to the API so a
    # caller can positively mark a job as non-parallel.
    parallel: bool | None = None
    # A job timestamp (per the /jobs endpoint). Sourced from COVERALLS_RUN_AT,
    # the config file, or a Coveralls() kwarg; when none is provided, resolve()
    # defaults it to the current time. This mirrors the official
    # coverallsapp/coverage-reporter, which reads COVERALLS_RUN_AT and falls
    # back to the current timestamp. Left None on a bare Config() (the default
    # is applied only through resolve(), the upload path).
    run_at: str | None = None

    # client settings
    # Comma-separated parallel-job flags to carry forward for missing jobs;
    # webhook/finish-only, so deliberately kept out of PAYLOAD_FIELDS (it is
    # sent by parallel_finish() to /webhook, never to the /jobs endpoint).
    carryforward: str | None = None
    host: str = DEFAULT_HOST
    skip_ssl_verify: bool = False
    token_required: bool = True
    base_dir: str = ''
    src_dir: str = ''
    # True lets coverage.py auto-discover its config file; a str names one.
    rcfile: str | bool = True
    timeout: float | None = None
    connect_timeout: float | None = None
    read_timeout: float | None = None
    retries: int = DEFAULT_RETRIES

    def __post_init__(self) -> None:
        self.timeout = self._validate_timeout('timeout', self.timeout)
        self.connect_timeout = self._validate_timeout(
            'connect_timeout', self.connect_timeout
        )
        self.read_timeout = self._validate_timeout(
            'read_timeout', self.read_timeout
        )
        self.retries = self._validate_retries(self.retries)

    @staticmethod
    def _validate_timeout(name: str, raw: Any) -> float | None:
        if raw is None:
            return None
        try:
            value = float(raw)
        except (TypeError, ValueError) as e:
            raise ValueError(
                f'Invalid {name} value {raw!r}: must be a number.'
            ) from e
        if value <= 0:
            raise ValueError(
                f'Invalid {name} value {raw!r}: must be greater than 0.'
            )
        return value

    @staticmethod
    def _validate_retries(raw: Any) -> int:
        # Only genuine ints and integer-valued strings (e.g. "3", from env vars
        # or YAML) are accepted. Bools are excluded despite being ints, so
        # retries=True is not silently read as 1; everything else is routed
        # through int(str(...)), which never truncates, so floats and
        # fractional strings (2.0, "1.5", "2.0") all raise.
        is_int = isinstance(raw, int) and not isinstance(raw, bool)
        try:
            value = int(raw) if is_int else int(str(raw))
        except (TypeError, ValueError) as e:
            raise ValueError(
                f'Invalid retries value {raw!r}: must be an integer.'
            ) from e
        if value < 0:
            raise ValueError(
                f'Invalid retries value {raw!r}: must not be negative.'
            )
        return value

    @property
    def request_timeout(self) -> tuple[float, float]:
        """
        Resolve the (connect, read) tuple passed to ``requests``.

        A phase-specific value wins for its phase; otherwise the overall
        ``timeout`` applies; otherwise the phase default is used.
        """
        connect = self.connect_timeout
        if connect is None:
            connect = self.timeout
        if connect is None:
            connect = DEFAULT_CONNECT_TIMEOUT

        read = self.read_timeout
        if read is None:
            read = self.timeout
        if read is None:
            read = DEFAULT_READ_TIMEOUT

        return (connect, read)

    def ensure_token(self) -> None:
        """Raise if an upload needs a repo token but none is configured."""
        if self.repo_token or not self.token_required:
            return

        if os.environ.get('GITHUB_ACTIONS'):
            raise RuntimeError(
                'Running on Github Actions but GITHUB_TOKEN is not set. Add '
                '"env: GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}" to your '
                'step config.'
            )

        raise RuntimeError(
            'No supported CI found and no repo token configured. You have to '
            f'provide repo_token in {TOML_CONFIG_FILE} ([tool.coveralls]) or '
            f'{YAML_CONFIG_FILE}, or set the COVERALLS_REPO_TOKEN env var.'
        )

    def to_payload(self) -> dict[str, Any]:
        """Build the subset of config that is submitted to the API."""
        # Include a field when it is set to anything other than None: an
        # explicitly-falsey value (parallel=False, a numeric 0 job id) is a
        # real choice and must be forwarded; only unset fields are dropped.
        return {
            name: value
            for name in PAYLOAD_FIELDS
            if (value := getattr(self, name)) is not None
        }


_FIELD_NAMES = frozenset(f.name for f in dataclasses.fields(Config))

# Permanent alternate spellings accepted in the config file and as Coveralls()
# keyword arguments. Both the canonical name and the alias are long-term
# supported and neither warns: ``coveralls_host`` reads more clearly in a
# config file, while ``host`` matches the ``COVERALLS_HOST`` env var and
# ``--host`` flag.
ALIASES = {'coveralls_host': 'host'}

# Renamed keys still accepted for backwards-compatibility but deprecated: they
# warn and will be removed in a future release.
DEPRECATED_KEYS = {'config_file': 'rcfile'}


def _canonicalize_keys(
    data: Mapping[str, Any], *, source: str
) -> dict[str, Any]:
    """
    Map alias/deprecated keys to their canonical names.

    Permanent aliases are mapped silently; deprecated keys additionally warn.
    An explicit canonical key in the same source always takes precedence.
    """
    result: dict[str, Any] = {}
    for key, value in data.items():
        canonical = ALIASES.get(key) or DEPRECATED_KEYS.get(key)
        if canonical is None:
            result[key] = value
            continue
        if key in DEPRECATED_KEYS:
            log.warning(
                '%r is deprecated and will be removed in a future release; '
                'use %r instead (in %s).',
                key,
                canonical,
                source,
            )
        if canonical not in data:
            result[canonical] = value
    return result


def _filter_known(data: Mapping[str, Any], *, source: str) -> dict[str, Any]:
    known = {}
    for key, value in data.items():
        if key in _FIELD_NAMES:
            known[key] = value
        else:
            log.warning(
                'Ignoring unknown config option %r from %s.', key, source
            )
    return known


def _canonicalize_and_filter(
    data: Mapping[str, Any], *, source: str
) -> dict[str, Any]:
    canonical = _canonicalize_keys(data, source=source)
    return _filter_known(canonical, source=source)
