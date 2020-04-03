Coveralls for Python
====================

:Test Status:
    .. image:: https://img.shields.io/circleci/project/github/coveralls-clients/coveralls-python/master.svg?style=flat-square&label=CircleCI
        :target: https://circleci.com/gh/coveralls-clients/coveralls-python

    .. image:: https://img.shields.io/travis/coveralls-clients/coveralls-python/master.svg?style=flat-square&label=TravisCI
        :target: https://travis-ci.org/coveralls-clients/coveralls-python

    .. image:: https://img.shields.io/github/workflow/status/coveralls-clients/coveralls-python/coveralls/master?style=flat-square&label=Github%20Actions
        :target: https://github.com/coveralls-clients/coveralls-python/actions

    .. image:: https://img.shields.io/coveralls/coveralls-clients/coveralls-python/master.svg?style=flat-square&label=Coverage
        :target: https://coveralls.io/r/coveralls-clients/coveralls-python

:Version Info:
    .. image:: https://img.shields.io/conda/v/conda-forge/coveralls?style=flat-square&label=Conda
        :target: https://anaconda.org/conda-forge/coveralls

    .. image:: https://img.shields.io/pypi/v/coveralls.svg?style=flat-square&label=PyPI
        :target: https://pypi.org/project/coveralls/

    .. image:: https://img.shields.io/conda/dn/conda-forge/coveralls?label=Conda%20Downloads&style=flat-square
        :target: https://anaconda.org/conda-forge/coveralls

    .. image:: https://img.shields.io/pypi/dm/coveralls.svg?style=flat-square&label=PyPI%20Downloads
        :target: https://pypi.org/project/coveralls/

:Compatibility:
    .. image:: https://img.shields.io/pypi/pyversions/coveralls.svg?style=flat-square&label=Python%20Versions
        :target: https://pypi.org/project/coveralls/

    .. image:: https://img.shields.io/pypi/implementation/coveralls.svg?style=flat-square&label=Python%20Implementations
        :target: https://pypi.org/project/coveralls/

`coveralls.io`_ is a service for publishing your coverage stats online. This
package provides seamless integration with `coverage.py`_ (and thus ``pytest``,
``nosetests``, etc...) in your Python projects::

    pip install coveralls
    coverage run --source=mypkg setup.py test
    coveralls

For more information and usage instructions, see our `documentation`_.

Version Compatibility
---------------------

As of version 2.0, we have dropped support for end-of-life'd versions of Python
and particularly old version of coverage. Support for non-EOL'd environments is
provided on a best-effort basis and will generally be removed once they make
maintenance too difficult.

If you're running on an outdated environment with a new enough package manager
to support version checks (see `the PyPA docs`_), then installing the latest
compatible version should do the trick. If you're even more outdated than that,
please pin to ``coveralls<2``.

If you're in an outdated environment and experiencing an issue, feel free to
open a ticket -- but please mention your environment! I'm willing to backport
fixes to the 1.x branch if need be.

.. _coveralls.io: https://coveralls.io/
.. _coverage.py: https://coverage.readthedocs.io/en/latest/
.. _documentation: http://coveralls-python.readthedocs.io/en/latest/
.. _the PyPA docs: https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires
