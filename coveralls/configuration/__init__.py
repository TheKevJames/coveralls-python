from collections.abc import Mapping
from typing import Any

from . import ci
from . import environment
from . import files
from . import helpers

Config = helpers.Config

__all__ = ['Config', 'resolve']


def resolve(
    overrides: Mapping[str, Any], *, token_required: bool = True
) -> Config:
    """
    Resolve configuration from all sources into a single typed Config.

    Precedence (later wins): CI environment, ``COVERALLS_*`` env vars, the
    config file, then explicit overrides (e.g. CLI flags).

    ``run_at`` additionally gains a computed default: when no source provides
    it, it is set to the current time (see :func:`default_run_at`).

    ``token_required`` is not a config value read from any of those sources: it
    is a guard against accidental tokenless uploads, calculated here from the
    caller's ``token_required`` argument (the CLI derives it from the
    ``--debug``/``--output`` flags) and waived automatically on a CI service
    that authenticates uploads itself. A ``token_required`` key in the config
    file or environment is therefore ignored.
    """
    # pylint: disable=protected-access
    overrides = helpers._canonicalize_keys(overrides, source='arguments')
    cleaned = helpers._filter_known(
        {key: value for key, value in overrides.items() if value is not None},
        source='arguments',
    )
    name, fields = ci._detect_ci()

    partials = [
        ci._from_ci_environment(name, fields),
        environment._from_environment(),
        files._from_files(),
        cleaned,
    ]

    merged: dict[str, Any] = {}
    for part in partials:
        merged.update(part)
    merged['token_required'] = (
        token_required and name not in ci.TOKENLESS_CI_SERVICES
    )
    # run_at is optional to the API (it timestamps on receipt when absent), but
    # the official reporter always sends one: default to now when no source set
    # it, matching coverallsapp/coverage-reporter's COVERALLS_RUN_AT-or-now.
    merged.setdefault('run_at', helpers.default_run_at())
    # Coerce the boolean flags: a config file may carry a non-bool (e.g. a
    # quoted ``parallel: "yes"``), which must not reach the API or a client
    # toggle as a stray string.
    for flag in ('parallel', 'skip_ssl_verify'):
        if flag in merged:
            merged[flag] = bool(merged[flag])

    return helpers.Config(**merged)
