# The config keys that belong in the JSON submitted to coveralls.io -- every
# job parameter the API accepts and lets the caller set. Everything else in the
# config (base_dir, src_dir, config_file, the timeout family, ...) controls
# local client behaviour and must never be sent: the uploaded payload already
# includes every source file, so leaking client-only settings is both noise and
# a needless disclosure.
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
