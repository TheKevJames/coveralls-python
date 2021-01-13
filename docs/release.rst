Release
=======

This project is released on PyPI as `coveralls`_.

To cut a new release, ensure the latest master passes all tests. Then, create a release commit:

#. Update the ``CHANGELOG.md`` with the new version (``clog -C CHANGELOG.md -F --setversion x.y.z``).
#. Bump the version number in ``version.py``.
#. Commit and push (``git commit -am 'chore(release): bump version' && git push``)
#. Tag and push that commit with the version number (``git tag x.y.z && git push origin x.y.z``).
#. Create a new `GitHub release`_.

To create a new PyPI release, do the following:

#. Build the sources (``python setup.py sdist bdist_wheel``).
#. Register & upload the sources. (``twine upload $PWD/dist/*``).

Then, to pin a new docker release, do the following:

#. Build the new image (``docker build --build-arg COVERALLS="coveralls==x.y.z" -t thekevjames/coveralls:x.y.z .``.
#. Push it to dockerhub (``docker push thekevjames/coveralls:x.y.z``).
#. Note: the ``:latest`` tag will be handled automatically by Dockerhub's automated infrastructure.

Conda should automatically create a PR on their `coveralls-feedstock`_ shortly with the updated version -- if something goes wrong, the manual process would be to:

#. Fork `coveralls-feedstock`_.
#. Update ``recipe/meta.yaml`` with the new version number and `sha`_.
#. Create a PR.
#. Comment on your own PR with: "@conda-forge-admin, please rerender".
#. Merge along with the automated commit from Conda.

.. _coveralls: https://pypi.org/project/coveralls/
.. _coveralls-feedstock: https://github.com/conda-forge/coveralls-feedstock
.. _GitHub release: https://github.com/TheKevJames/coveralls-python/releases/new
.. _sha: https://pypi.org/project/coveralls/#files
