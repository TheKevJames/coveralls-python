import sys

__all__ = ["test_func"]

if sys.version_info[:2] >= (3, 10):
    from bar_310 import test_func
else:
    from bar import test_func
