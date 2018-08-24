.. _vcsconfig:

VCS Configuration
=================

``coveralls-python`` supports ``git`` by default and will run the necessary ``git`` commands to collect the required information without any intervention.

As describe in `the coveralls docs`_, you may also configure these values by setting environment variables. These will be used in the fallback case, eg. if ``git`` is not available or your project is not a ``git`` repository.

As described in the linked documentation, you can also use this method to support non- ``git`` projects::

    GIT_ID=$(hg tip --template '{node}\n')
    GIT_AUTHOR_NAME=$(hg tip --template '{author|person}\n')
    GIT_AUTHOR_EMAIL=$(hg tip --template '{author|email}\n')
    GIT_COMMITTER_NAME=$(hg tip --template '{author|person}\n')
    GIT_COMMITTER_EMAIL=$(hg tip --template '{author|email}\n')
    GIT_MESSAGE=$(hg tip --template '{desc}\n')
    GIT_BRANCH=$(hg branch)

.. _the coveralls docs: https://docs.coveralls.io/mercurial-support
