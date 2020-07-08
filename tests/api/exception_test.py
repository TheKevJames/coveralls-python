# pylint: disable=no-self-use
import logging
import unittest

import pytest

from coveralls.exception import CoverallsException

class CoverallsExceptionTest(unittest.TestCase):

    _caplog = None

    @pytest.fixture(autouse=True)
    def inject_fixtures(self, caplog):
        self._caplog = caplog

    def test_log(self):
        self._caplog.set_level(logging.INFO)
        exc_value = ''
        try:
            raise CoverallsException('Some exception')
        except CoverallsException as e:
            logging.exception('Found exception')
            assert 'raise CoverallsException(' in \
                self._caplog.text
            exc_value = str(e)

        assert exc_value == 'Some exception'

    def test_eq(self):
        exc1 = CoverallsException('Value1')
        exc2 = CoverallsException('Value1')
        assert exc1 == exc2
        assert not exc1 == 35  # pylint: disable=unneeded-not
        assert exc1 is not exc2

    def test_ne(self):
        exc1 = CoverallsException('Value1')
        exc2 = CoverallsException('Value2')
        assert exc1 != exc2
        assert exc1 is not exc2
