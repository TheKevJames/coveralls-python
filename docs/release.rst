Release
=======

This project is released on PyPI as `coveralls`_.

To cut a new release, ensure the latest master passes all tests. Then, create a release commit:

1. Update the ``CHANGELOG.md`` with the new version (``clog -C CHANGELOG.md -F --setversion x.y.z``).
2. Bump the version number in ``version.py``.
3. Tag that commit with the version number (``git tag x.y.z``).
4. Push the new tag to GitHub.
5. Create a new `GitHub release`_.

Make sure to push the release commit to GitHub.

To create a new PyPI release, do the following:

1. Build the sources (``python setup.py sdist bdist_wheel``).
2. Register & upload the sources. (``twine upload dist/*``).

To create a new Conda Forge release, do the following:

1. Fork `coveralls-feedstock`_.
2. Update ``recipe/meta.yaml`` with the new version number and `sha`_.
3. Create a PR. A conda-forge maintainer will get to it eventually.

.. _coveralls: https://pypi.org/project/coveralls/
.. _coveralls-feedstock: https://github.com/conda-forge/coveralls-feedstock
.. _GitHub release: https://github.com/coveralls-clients/coveralls-python/releases/new
.. _sha: https://pypi.org/project/coveralls/#files
