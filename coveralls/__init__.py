import importlib.metadata

from .api import Coveralls


__version__ = importlib.metadata.version('coveralls')
__all__ = ['Coveralls']
