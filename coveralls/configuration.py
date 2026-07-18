import dataclasses
from typing import Any

from .exception import CoverallsException


DEFAULT_HOST = 'https://coveralls.io/'

# requests has no wall-clock "total" timeout: a scalar applies separately to
# the connect and read phases. We always resolve an explicit (connect, read)
# tuple so a stalled endpoint can never hang the CLI indefinitely.
DEFAULT_CONNECT_TIMEOUT = 10
DEFAULT_READ_TIMEOUT = 60

# Fields sent to the coveralls.io API. Everything else on Config controls local
# client behaviour and must never enter the submitted payload.
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
    service_name: str | None = None
    service_number: str | None = None
    service_job_id: str | None = None
    service_job_number: str | None = None
    service_pull_request: str | None = None
    service_branch: str | None = None
    service_build_url: str | None = None
    flag_name: str | None = None
    parallel: bool = False

    # client settings
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

    def __post_init__(self) -> None:
        self.timeout = self._validate_timeout('timeout', self.timeout)
        self.connect_timeout = self._validate_timeout(
            'connect_timeout', self.connect_timeout,
        )
        self.read_timeout = self._validate_timeout(
            'read_timeout', self.read_timeout,
        )

    @staticmethod
    def _validate_timeout(name: str, raw: Any) -> float | None:
        if raw is None:
            return None
        try:
            value = float(raw)
        except (TypeError, ValueError) as e:
            raise CoverallsException(
                f'Invalid {name} value {raw!r}: must be a number.',
            ) from e
        if value <= 0:
            raise CoverallsException(
                f'Invalid {name} value {raw!r}: must be greater than 0.',
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

    def to_payload(self) -> dict[str, Any]:
        """Build the subset of config that is submitted to the API."""
        return {
            name: value
            for name in PAYLOAD_FIELDS
            if (value := getattr(self, name))
        }
