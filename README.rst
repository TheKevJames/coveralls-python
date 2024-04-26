Coveralls for Python
====================

.. raw:: html

    <div>
        <strong>Test Status:</strong>
        <a href="https://circleci.com/gh/TheKevJames/coveralls-python"><img src="https://img.shields.io/circleci/project/github/TheKevJames/coveralls-python/master.svg?style=flat-square&label=CircleCI"/></a>
        <a href="https://github.com/TheKevJames/coveralls-python/actions"><img src="https://img.shields.io/github/actions/workflow/status/TheKevJames/coveralls-python/test.yml?branch=master&style=flat-square&label=Github%20Actions"/></a>
        <a href="https://coveralls.io/r/TheKevJames/coveralls-python"><img src="https://img.shields.io/coveralls/TheKevJames/coveralls-python/master.svg?style=flat-square&label=Coverage"/></a>
        <a href="http://coveralls-python.readthedocs.io/en/latest/"><img src="https://img.shields.io/readthedocs/coveralls-python?style=flat-square&label=Docs"/></a>
    </div>
    <br/>
    <div>
        <strong>Version Info:</strong>
        <a href="https://pypi.org/project/coveralls/"><img src="https://img.shields.io/pypi/v/coveralls.svg?style=flat-square&label=PyPI"/></a>
        <a href="https://anaconda.org/conda-forge/coveralls"><img src="https://img.shields.io/conda/v/conda-forge/coveralls?style=flat-square&label=Conda"/></a>
        <a href="https://hub.docker.com/r/thekevjames/coveralls"><img src="https://img.shields.io/docker/v/thekevjames/coveralls?sort=semver&style=flat-square&label=Dockerhub"/></a>
        <a href="https://quay.io/repository/thekevjames/coveralls"><img src="https://img.shields.io/docker/v/thekevjames/coveralls?sort=semver&style=flat-square&label=Quay"/></a>
    </div>
    <br/>
    <div>
        <strong>Compatibility:</strong>
        <a href="https://pypi.org/project/coveralls/"><img src="https://img.shields.io/pypi/pyversions/coveralls.svg?style=flat-square&label=Python%20Versions"/></a>
        <a href="https://pypi.org/project/coveralls/"><img src="https://img.shields.io/pypi/implementation/coveralls.svg?style=flat-square&label=Python%20Implementations"/></a>
    </div>
    <br/>
    <div>
        <strong>Downloads:</strong>
        <a href="https://pypi.org/project/coveralls/"><img src="https://img.shields.io/pypi/dm/coveralls.svg?style=flat-square&label=PyPI"/></a>
        <a href="https://pypi.org/project/coveralls/"><img src="https://img.shields.io/conda/dn/conda-forge/coveralls?style=flat-square&label=Conda"/></a>
        <a href="https://hub.docker.com/r/thekevjames/coveralls"><img src="https://img.shields.io/docker/pulls/thekevjames/coveralls?style=flat-square&label=Dockerhub"/></a>
    </div>
    <br/>

`coveralls.io`_ is a service for publishing your coverage stats online. This
package provides seamless integration with `coverage.py`_ (and thus ``pytest``,
``nosetests``, etc...) in your Python projects::

    pip install coveralls
    coverage run --source=mypkg -m pytest tests/
    coveralls

For more information and usage instructions, see our `documentation`_.

Version Compatibility
---------------------

As of version 2.0, we have dropped support for end-of-life'd versions of Python
and particularly old versions of coverage. Support for non-EOL'd environments
is provided on a best-effort basis and will generally be removed once they make
maintenance too difficult.

If you're running on an outdated environment with a new enough package manager
to support version checks (see `the PyPA docs`_), then installing the latest
compatible version should do the trick automatically! If you're even more
outdated than that, please pin to ``coveralls<2``.

If you're in an outdated environment and experiencing an issue, you're welcome
to open a ticket -- but please mention your environment! I'm willing to
backport fixes to the 1.x branch if the need is great enough.

.. _Docs: http://coveralls-python.readthedocs.io/en/latest/
.. _coverage.py: https://coverage.readthedocs.io/en/latest/
.. _coveralls.io: https://coveralls.io/
.. _documentation: http://coveralls-python.readthedocs.io/en/latest/
.. _the PyPA docs: https://packaging.python.org/guides/distributing-packages-using-setuptools/#python-requires
