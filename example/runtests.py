from project import branch  # type: ignore[import-not-found]
from project import hello

if __name__ == '__main__':
    hello()
    branch(False, True)
    branch(True, True)
