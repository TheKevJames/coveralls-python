Usage Within Tox
================

Running coveralls-python from within a `tox`_ environment (v2.0 and above) requires an additional step; since coveralls-python relies on environment variables to function, you'll need to configure tox to capture those variables using the ``passenv`` configuration option in your ``tox.ini``.

For example, on TravisCI::

    [tox]
    envlist = py27,py33,py34

    [testenv]
    passenv = TRAVIS TRAVIS_JOB_ID TRAVIS_BRANCH
    deps =
        coveralls
    commands =
        coverage run --source=yourpackagename setup.py test
        coveralls

If you are configuring coveralls-python with environment variables, you should also pass those. See `configuration <configuration.rst>`_ for more details.

AppVeyor
--------
::

    passenv = APPVEYOR APPVEYOR_BUILD_ID APPVEYOR_REPO_BRANCH APPVEYOR_PULL_REQUEST_NUMBER

BuildKite
---------
::

    passenv = BUILDKITE BUILDKITE_JOB_ID BUILDKITE_BRANCH

CircleCI
--------
::

    passenv = CIRCLECI CIRCLE_BUILD_NUM CIRCLE_BRANCH CI_PULL_REQUEST

Jenkins
-------
::

    passenv = JENKINS_HOME BUILD_NUMBER GIT_BRANCH CI_PULL_REQUEST

TravisCI
--------
::

    passenv = TRAVIS TRAVIS_JOB_ID TRAVIS_BRANCH TRAVIS_PULL_REQUEST

.. _tox: https://tox.readthedocs.io/en/latest/
