Configuration
=============

coveralls-python often works without any outside configuration by examining the environment it is being run in. Special handling has been added for AppVeyor, BuildKite, CircleCI, and TravisCI to make coveralls-python as close to "plug and play" as possible.

Most often, you will simply need to run coveralls-python with no additional options after you have run your coverage suite::

    $ coveralls

If you have placed your ``.coveragerc`` in a non-standard location, you can run::

    $ coveralls --rcfile=/path/to/coveragerc

If you are interested in merging the coverage results between multiple languages/projects, see our :ref:`multilang` documentation.

If coveralls-python is being run on CircleCI or TravisCI, it will automatically set the token for communication with coveralls.io. Otherwise, you should set the environment variable ``COVERALLS_REPO_TOKEN``, which can be found on the dashboard for your project in coveralls.io::

    $ COVERALLS_REPO_TOKEN=mV2Jajb8y3c6AFlcVNagHO20fiZNkXPVy coveralls

If you are running multiple jobs in parallel and want coveralls.io to merge those results, you should set ``COVERALLS_PARALLEL`` to ``true`` in your environment and run::

    $ COVERALLS_PARALLEL=true coveralls

You can also set any of these values in a ``.coveralls.yml`` file in the root of your project repository. If you are planning to use this method, please ensure you install ``coveralls[yaml]`` instead of just the base ``coveralls`` package.

Sample ``.coveralls.yml`` file::

    service_name: travis-pro
    repo_token: mV2Jajb8y3c6AFlcVNagHO20fiZNkXPVy
    parallel: true
