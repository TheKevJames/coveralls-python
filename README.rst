Coveralls for python
====================

.. image:: https://img.shields.io/circleci/project/github/coveralls-clients/coveralls-python/master.svg?style=flat-square
    :target: https://circleci.com/gh/coveralls-clients/coveralls-python

.. image:: https://img.shields.io/travis/coveralls-clients/coveralls-python/master.svg?style=flat-square
    :target: https://travis-ci.org/coveralls-clients/coveralls-python

.. image:: https://img.shields.io/coveralls/coveralls-clients/coveralls-python/master.svg?style=flat-square
    :target: https://coveralls.io/r/coveralls-clients/coveralls-python

.. image:: https://img.shields.io/pypi/v/coveralls.svg?style=flat-square
    :target: https://pypi.python.org/pypi/coveralls

.. image:: https://img.shields.io/pypi/pyversions/coveralls.svg?style=flat-square
    :target: https://pypi.python.org/pypi/coveralls

.. image:: https://img.shields.io/pypi/implementation/coveralls.svg?style=flat-square
    :target: https://pypi.python.org/pypi/coveralls

`coveralls.io`_ is a service for publishing your coverage stats online. This package provides seamless integration with `coverage.py`_ (and thus ``py.test``, ``nosetests``, etc...) in your Python projects::

    pip install coveralls
    coverage run --source=mypkg setup.py test
    coveralls

For more information and usage instructions, see our `documentation`_.

.. _coveralls.io: https://coveralls.io/
.. _coverage.py: https://coverage.readthedocs.io/en/latest/
.. _documentation: http://coveralls-python.readthedocs.io/en/latest/
