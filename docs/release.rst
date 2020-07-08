Release
=======

This project is released on PyPI as `coveralls`_.

To cut a new release, ensure the latest master passes all tests. Then, create a release commit:

1. Update the ``CHANGELOG.md`` with the new version (``clog -C CHANGELOG.md -F --setversion x.y.z``).
2. Bump the version number in ``version.py``.
3. Commit and push (``git commit -am 'chore(release): bump version' && git push``)
4. Tag that commit with the version number (``git tag x.y.z``).
5. Push the new tag to GitHub.
6. Create a new `GitHub release`_.

To create a new PyPI release, do the following:

1. Build the sources (``python setup.py sdist bdist_wheel``).
2. Register & upload the sources. (``twine upload $PWD/dist/*``).

Conda should automatically create a PR on their `coveralls-feedstock`_ shortly with the updated version -- if something goes wrong, the manual process would be to:

1. Fork `coveralls-feedstock`_.
2. Update ``recipe/meta.yaml`` with the new version number and `sha`_.
3. Create a PR.
4. Comment on your own PR with: "@conda-forge-admin, please rerender".
5. Merge along with the automated commit from Conda.

.. _coveralls: https://pypi.org/project/coveralls/
.. _coveralls-feedstock: https://github.com/conda-forge/coveralls-feedstock
.. _GitHub release: https://github.com/coveralls-clients/coveralls-python/releases/new
.. _sha: https://pypi.org/project/coveralls/#files
