Release
=======

This project is released on PyPI as `coveralls`_, as well as on `quay`_ and `dockerhub`_.

To cut a new release, ensure the latest master passes all tests. Then, create a release commit:

#. Update the ``CHANGELOG.md`` with the new version (``clog -C CHANGELOG.md -F --setversion x.y.z``).
#. Bump the version number with poetry: ``poetry version (major|minor|patch)``.
#. Commit and push (``git commit -am 'chore(release): bump version' && git push``)
#. Tag and push that commit with the version number (``git tag x.y.z && git push origin x.y.z``).
#. Create a new `GitHub release`_.
#. Verify the `docs build succeeded`_ then `mark it active`_.

Conda should automatically create a PR on their `coveralls-feedstock`_ shortly with the updated version -- if something goes wrong, the manual process would be to:

#. Fork `coveralls-feedstock`_.
#. Update ``recipe/meta.yaml`` with the new version number and `sha`_.
#. Create a PR.
#. Comment on your own PR with: "@conda-forge-admin, please rerender".
#. Merge along with the automated commit from Conda.

Note that the ``clog`` command comes from ``cargo install clog-cli``.

.. _GitHub release: https://github.com/TheKevJames/coveralls-python/releases/new
.. _coveralls-feedstock: https://github.com/conda-forge/coveralls-feedstock
.. _coveralls: https://pypi.org/project/coveralls/
.. _dockerhub: https://hub.docker.com/r/thekevjames/coveralls
.. _docs build succeeded: https://readthedocs.org/projects/coveralls-python/builds/
.. _mark it active: https://readthedocs.org/projects/coveralls-python/versions/
.. _quay: https://quay.io/repository/thekevjames/coveralls
.. _sha: https://pypi.org/project/coveralls/#files
