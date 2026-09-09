import importlib.metadata

from .api import Coveralls  # noqa: IMR241

__version__ = importlib.metadata.version('coveralls')
__all__ = ['Coveralls']
