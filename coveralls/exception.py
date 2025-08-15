class CoverallsException(Exception):
    # TODO: do we really need this?
    def __eq__(self, other) -> bool:
        if isinstance(other, self.__class__):
            return str(self) == str(other)
        return False

    def __ne__(self, other) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(str(self))
