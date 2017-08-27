Release
=======

This project is released on PyPI as `coveralls`_.

To cut a new release, ensure the latest master passes all tests. Then, create a release commit:

1. Update the :code:`CHANGELOG.md` with the new version (:code:`clog -C CHANGELOG.md -F --setversion x.y.z`).
2. Bump the version number in :code:`version.py`.
3. Tag that commit with the version number (:code:`git tag x.y.z`).
4. Push the new tag to GitHub.
5. Create a new `GitHub release`_.

Make sure to push the release commit to GitHub.

To create a new PyPI release, do the following:

1. Build the sources (:code:`python setup.py sdist bdist_wheel`).
2. Register & upload the sources. (:code:`twine upload dist/*`).

NOTE: in the future, we may want to expand this to include other sources, such as eggs for various Python versions. Since we already test with :code:`tox`, this could be as simple as::

    .tox/py34/bin/python setup.py bdist_egg
    .tox/py35/bin/python setup.py bdist_egg
    # etc

.. _`coveralls`: https://pypi.org/project/coveralls/
.. _`GitHub release`: https://github.com/coveralls-clients/coveralls-python/releases/new
