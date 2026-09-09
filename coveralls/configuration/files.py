import logging
import pathlib
import sys
from collections.abc import Mapping
from typing import Any

from . import helpers

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


log = logging.getLogger('coveralls.configuration.files')


def _read_yaml() -> dict[str, Any] | None:
    """
    Read the raw ``.coveralls.yml`` mapping, or None when it has no settings.

    Returns None (rather than an empty dict) when the file is absent, empty, or
    unreadable because PyYAML is missing, so :func:`_from_files` can tell "this
    source provided settings" from "this source is silent" and pick a winner.
    """
    path = pathlib.Path.cwd() / helpers.YAML_CONFIG_FILE
    if not path.exists():
        return None

    try:
        import yaml  # pylint: disable=import-outside-toplevel
    except ImportError:
        log.warning(
            'PyYAML is not installed, skipping %s.', helpers.YAML_CONFIG_FILE
        )
        return None

    data = yaml.safe_load(path.read_text(encoding='utf-8'))
    return data or None


def _read_toml() -> dict[str, Any] | None:
    """
    Read the raw ``[tool.coveralls]`` mapping from ``pyproject.toml``.

    Returns None when the file or table is absent/empty. A malformed file
    surfaces as :class:`tomllib.TOMLDecodeError`; a ``tool.coveralls`` that is
    present but not a table is a configuration error and raises ``TypeError``.
    """
    path = pathlib.Path.cwd() / helpers.TOML_CONFIG_FILE
    if not path.exists():
        return None

    with path.open('rb') as handle:
        data = tomllib.load(handle)

    section = data.get('tool', {}).get('coveralls')
    if section is None:
        return None
    if not isinstance(section, Mapping):
        raise TypeError(
            f'Invalid [tool.coveralls] in {helpers.TOML_CONFIG_FILE}: '
            f'expected a table, got {type(section).__name__}.'
        )
    return dict(section) or None


def _from_files() -> dict[str, Any]:
    """
    Load the single winning config file.

    Config files are never merged: the first source with settings wins, and
    the legacy ``.coveralls.yml`` takes precedence over ``pyproject.toml``
    (matching the community norm where a dedicated file beats pyproject.toml).
    Only the winner is canonicalized/filtered, so unknown-key warnings are not
    emitted for a file whose values are discarded.
    """
    # pylint: disable=protected-access
    yaml_config = _read_yaml()
    toml_config = _read_toml()

    if yaml_config is not None and toml_config is not None:
        log.warning(
            'Both %s and [tool.coveralls] in %s were found; using %s and '
            'ignoring %s. The YAML config is legacy -- consider consolidating '
            'into %s.',
            helpers.YAML_CONFIG_FILE,
            helpers.TOML_CONFIG_FILE,
            helpers.YAML_CONFIG_FILE,
            helpers.TOML_CONFIG_FILE,
            helpers.TOML_CONFIG_FILE,
        )

    if yaml_config is not None:
        return helpers._canonicalize_and_filter(
            yaml_config, source=helpers.YAML_CONFIG_FILE
        )
    if toml_config is not None:
        source = f'{helpers.TOML_CONFIG_FILE} [tool.coveralls]'
        return helpers._canonicalize_and_filter(toml_config, source=source)
    return {}
