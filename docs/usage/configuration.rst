.. _configuration:

Configuration
=============

coveralls-python often works without any outside configuration by examining the environment it is being run in. Special handling has been added for AppVeyor, BuildKite, CircleCI, Github Actions, Jenkins, and TravisCI to make coveralls-python as close to "plug and play" as possible.

Most often, you will simply need to run coveralls-python with no additional options after you have run your coverage suite::

    coveralls

If you have placed your ``.coveragerc`` in a non-standard location, you can run::

    coveralls --rcfile=/path/to/coveragerc

If you would like to override the service name (auto-discovered on most CI systems, set to ``coveralls-python`` otherwise)::

    coveralls --service=travis-pro
    # or, via env var:
    COVERALLS_SERVICE_NAME=travis-pro coveralls

If you are interested in merging the coverage results between multiple languages/projects, see our :ref:`multi-language <multilang>` documentation.

If coveralls-python is being run on TravisCI, it will automatically set the token for communication with coveralls.io. Otherwise, you should set the environment variable ``COVERALLS_REPO_TOKEN``, which can be found on the dashboard for your project in coveralls.io::

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

Github Actions Gotcha
---------------------

Coveralls natively supports jobs running on Github Actions. You can directly pass the default-provided secret GITHUB_TOKEN::

    env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
    run: |
        coveralls

For parallel builds, you have to add a final step to let coveralls know the parallel build is finished. You also have to set COVERALLS_FLAG_NAME to something unique to the specific step, so re-runs of the same job don't keep piling up builds::

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
            uses: actions/checkout@v2
          - name: Test
            run: ./run_tests.sh ${{ matrix.test-name }}
          - name: Upload Coverage
            run: coveralls
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
              COVERALLS_FLAG_NAME: ${{ matrix.test-name }}
              COVERALLS_PARALLEL: true
      coveralls:
        name: Finish Coveralls
        needs: test
        runs-on: ubuntu-latest
        container: python:3-slim
        steps:
        - name: Finished
          run: |
            pip3 install --upgrade coveralls
            coveralls --finish
          env:
            GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
