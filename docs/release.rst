Changelog
=========

``CHANGELOG.md`` is generated from the git history by `git cliff`_ at release
time. Each commit becomes a single bullet (its subject line); For a non-trivial
change, add a ``changelog:`` footer to the commit message and it will render
any text beneath the bullet. It must be the last footer in the message::

    feat(api): add configurable request timeouts

    (Optional body prose, notes to reviewers, etc. -- not shown in the changelog.)

    changelog:
    Requests now time out after 60s by default, configurable via
    ``--timeout`` or ``COVERALLS_TIMEOUT``.

See ``cliff.toml`` for the template and grouping rules.

Release
=======

This project is released on PyPI as `coveralls`_, as well as on `quay`_ and
`dockerhub`_. To cut a new release, ensure the latest master passes all tests.
Then, create a release commit. Bumping the version first lets ``git cliff``
stamp the new ``CHANGELOG.md`` section with it and prepend it in place:

.. code-block:: bash

    poetry version (major|minor|patch)
    git cliff --unreleased --tag "$(poetry version | cut -f2 -d' ')" --prepend CHANGELOG.md
    # touch up changelog here, if need be
    poetry lock --regenerate
    poetry sync
    poetry run pytest
    git commit -am 'chore(release): bump version'
    git push
    git tag $(poetry version | cut -f2 -d' ')
    git push origin $(poetry version | cut -f2 -d' ')

Then:

#. Create a new `GitHub release`_.
#. Verify the `docs build succeeded`_ then `mark it active`_.

Conda should automatically create a PR on their `coveralls-feedstock`_ shortly
with the updated version -- if something goes wrong, the manual process would
be to:

#. Fork `coveralls-feedstock`_.
#. Update ``recipe/meta.yaml`` with the new version number and `sha`_.
#. Create a PR.
#. Comment on your own PR with: "@conda-forge-admin, please rerender".
#. Merge along with the automated commit from Conda.

.. _GitHub release: https://github.com/TheKevJames/coveralls-python/releases/new
.. _git cliff: https://git-cliff.org/
.. _coveralls-feedstock: https://github.com/conda-forge/coveralls-feedstock
.. _coveralls: https://pypi.org/project/coveralls/
.. _dockerhub: https://hub.docker.com/r/thekevjames/coveralls
.. _docs build succeeded: https://readthedocs.org/projects/coveralls-python/builds/
.. _mark it active: https://readthedocs.org/projects/coveralls-python/versions/
.. _quay: https://quay.io/repository/thekevjames/coveralls
.. _sha: https://pypi.org/project/coveralls/#files
