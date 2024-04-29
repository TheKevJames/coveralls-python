.. _configuration:

Configuration
=============

coveralls-python often works without any outside configuration by examining the
environment it is being run in. Special handling has been added for AppVeyor,
BuildKite, CircleCI, Github Actions, Jenkins, and TravisCI to make
coveralls-python as close to "plug and play" as possible. It should be useable
in any other CI system as well, but may need some configuration!

In cases where you do need to modify the configuration, we obey a very strict
precedence order where the **latest value is used**:

* first, the CI environment will be loaded
* second, any environment variables will be loaded (eg. those which begin with
  ``COVERALLS_``
* third, the config file is loaded (eg. ``./..coveralls.yml``)
* finally, any command line flags are evaluated

Most often, you will simply need to run coveralls-python with no additional
options after you have run your coverage suite::

    coveralls

If you have placed your ``.coveragerc`` in a non-standard location (ie. other than ``./.coveragerc``), you can run::

    coveralls --rcfile=/path/to/coveragerc

If you would like to override the service name (auto-discovered on most CI systems, set to ``coveralls-python`` otherwise)::

    coveralls --service=travis-pro
    # or, via env var:
    COVERALLS_SERVICE_NAME=travis-pro coveralls

If you are interested in merging the coverage results between multiple languages/projects, see our :ref:`multi-language <multilang>` documentation.

If coveralls-python is being run on TravisCI or on GitHub Actions, it will automatically set the token for communication with coveralls.io. Otherwise, you should set the environment variable ``COVERALLS_REPO_TOKEN``, which can be found on the dashboard for your project in coveralls.io::

    COVERALLS_REPO_TOKEN=mV2Jajb8y3c6AFlcVNagHO20fiZNkXPVy coveralls

If you are running multiple jobs in parallel and want coveralls.io to merge those results, you should set ``COVERALLS_PARALLEL`` to ``true`` in your environment::

    COVERALLS_PARALLEL=true coveralls

Later on, you can use ``coveralls --finish`` to let the Coveralls service know you have completed all your parallel runs::

    coveralls --finish

If you are using a non-public coveralls.io instance (for example: self-hosted Coveralls Enterprise), you can set ``COVERALLS_HOST`` to the base URL of that insance::

    COVERALLS_HOST="https://coveralls.aperture.com" coveralls

In that case, you may also be interested in disabling SSL verification::

    COVERALLS_SKIP_SSL_VERIFY='1' coveralls

If you are using named jobs, you can set::

    COVERALLS_FLAG_NAME="insert-name-here"

You can also set any of these values in a ``.coveralls.yml`` file in the root of your project repository. If you are planning to use this method, please ensure you install ``coveralls[yaml]`` instead of just the base ``coveralls`` package.

Sample ``.coveralls.yml`` file::

    service_name: travis-pro
    repo_token: mV2Jajb8y3c6AFlcVNagHO20fiZNkXPVy
    parallel: true
    coveralls_host: https://coveralls.aperture.com

Github Actions support
----------------------

Coveralls natively supports jobs running on Github Actions. You can directly
pass the default-provided secret GITHUB_TOKEN::

    run: coveralls
    env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

Passing a coveralls.io token via the ``COVERALLS_REPO_TOKEN`` environment variable
(or via the ``repo_token`` parameter in the config file) is not needed for
Github Actions by default (eg. with the default value of ``--service=github``).

Github Actions can get a bit finicky as to how coverage is submitted. If you
find yourself getting 422 error responses, you can also try specifying the
``github-actions`` service name instead. If you do so, you will need to proved
a ``COVERALLS_REPO_TOKEN`` *instead* of a ``GITHUB_TOKEN``::

    run: coveralls --service=github-actions
    env:
        COVERALLS_REPO_TOKEN: ${{ secrets.COVERALLS_REPO_TOKEN }}

If you're still having issues after tryingt both of the above, please read through
the following issues for more information:
`#252 <https://github.com/TheKevJames/coveralls-python/issues/252>`_ and
`coveralls-public#1710 <https://github.com/lemurheavy/coveralls-public/issues/1710>`_.

For parallel builds, you have to add a final step to let coveralls.io know the
parallel build is finished::

    jobs:
      test:
        strategy:
          matrix:
            test-name:
              - test1
              - test2
        runs-on: ubuntu-latest
        steps:
          - name: Checkout
            uses: actions/checkout@v4
          - name: Test
            run: ./run_tests.sh ${{ matrix.test-name }}
          - name: Upload coverage data to coveralls.io
            run: coveralls
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
              COVERALLS_FLAG_NAME: ${{ matrix.test-name }}
              COVERALLS_PARALLEL: true
      coveralls:
        name: Indicate completion to coveralls.io
        needs: test
        runs-on: ubuntu-latest
        container: python:3-slim
        steps:
        - name: Install coveralls
          run: pip3 install --upgrade coveralls
        - name: Finished
          run: coveralls --finish
          env:
            GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

The ``COVERALLS_FLAG_NAME`` environment variable (or the ``flag_name`` parameter
in the config file) is optional and can be used to better identify each job
on coveralls.io. It does not need to be unique across the parallel jobs.

Azure Pipelines support
-----------------------

Coveralls does not yet support Azure Pipelines, but you can make things work by
impersonating another CI system such as CircleCI. For example, you can set this
up by using the following script at the end of your test pipeline::

    - script: |
        pip install coveralls
        export CIRCLE_BRANCH=$BUILD_SOURCEBRANCH
        coveralls
      displayName: 'coveralls'
      env:
        CIRCLECI: 1
        CIRCLE_BUILD_NUM: $(Build.BuildNumber)
        COVERALLS_REPO_TOKEN: $(coveralls_repo_token)

Note that you will also need to use the Azure Pipelines web UI to add the
``coveralls_repo_token`` variable to this pipeline with your repo token (which
you can copy from the coveralls.io website).

As per `#245 <https://github.com/TheKevJames/coveralls-python/issues/245>`_,
our users suggest leaving "keep this value secret" unchecked -- this may be
secure enough as-is, in that a user making a PR cannot access this variable.

Other CI systems
----------------

As specified in the Coveralls `official docs
<https://docs.coveralls.io/supported-ci-services>`
other CI systems can be supported if the following environment variables are
defined::

    CI_NAME
        # Name of the CI service being used.
    CI_BUILD_NUMBER
        # The number assigned to the build by your CI service.
    CI_BUILD_URL
        # URL to a webpage showing the build information/logs.
    CI_BRANCH
        # For pull requests this is the name of the branch being targeted,
        # otherwise it corresponds to the name of the current branch or tag.
    CI_JOB_ID (optional)
        # For parallel builds, the number assigned to each job comprising the build.
        # When missing, Coveralls will assign an incrementing integer (1, 2, 3 ...).
        # This value should not change between multiple runs of the build.
    CI_PULL_REQUEST (optional)
        # If given, corresponds to the number of the pull request, as specified
        # in the supported repository hosting service (GitHub, GitLab, etc).
        # This variable expects a value defined as an integer, e.g.:
        #   CI_PULL_REQUEST=42             (recommended)
        # However, for flexibility, any single line string ending with the same
        # integer value can also be used (such as the pull request URL or
        # relative path), e.g.:
        #   CI_PULL_REQUEST='myuser/myrepo/pull/42'
        #   CI_PULL_REQUEST='https://github.com/myuser/myrepo/pull/42'
