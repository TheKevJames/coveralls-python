import os
from typing import Any


def _from_environment() -> dict[str, Any]:
    config: dict[str, Any] = {}

    host = os.environ.get('COVERALLS_HOST')
    if host:
        config['host'] = host
    if os.environ.get('COVERALLS_PARALLEL', '').lower() == 'true':
        config['parallel'] = True
    if os.environ.get('COVERALLS_SKIP_SSL_VERIFY'):
        config['skip_ssl_verify'] = True

    fields = {
        'COVERALLS_BASE_DIR': 'base_dir',
        'COVERALLS_CONNECT_TIMEOUT': 'connect_timeout',
        'COVERALLS_FLAG_NAME': 'flag_name',
        'COVERALLS_RCFILE': 'rcfile',
        'COVERALLS_READ_TIMEOUT': 'read_timeout',
        'COVERALLS_REPO_TOKEN': 'repo_token',
        'COVERALLS_RETRIES': 'retries',
        'COVERALLS_RUN_AT': 'run_at',
        'COVERALLS_SERVICE_JOB_ID': 'service_job_id',
        'COVERALLS_SERVICE_JOB_NUMBER': 'service_job_number',
        'COVERALLS_SERVICE_NAME': 'service_name',
        'COVERALLS_SERVICE_NUMBER': 'service_number',
        'COVERALLS_SRC_DIR': 'src_dir',
        'COVERALLS_TIMEOUT': 'timeout',
    }
    for var, key in fields.items():
        value = os.environ.get(var)
        if value:
            config[key] = value

    return config
