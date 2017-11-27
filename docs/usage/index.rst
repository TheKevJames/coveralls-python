Usage
=====

This package works with any CI environment. Special handling has been included for some CI service providers, but coveralls-python can run anywhere.

To get started with coveralls-python, make sure to `add your repo`_ on the coveralls.io website. If you will be using coveralls-python on CircleCI or TravisCI, you're done here -- otherwise, take note of the "repo token" in the coveralls.io dashboard.

After that, its as simple as installing coveralls-python, collecting coverage results, and sending them to coveralls.io.

For example::

    pip install coveralls
    coverage run --source=my_package setup.py test
    COVERALLS_REPO_TOKEN=tGSdG5Qcd2dcQa2oQN9GlJkL50wFZPv1j coveralls

coveralls-python can be configured with several environment variables, as seen above. See :ref:`configuration` for more details.

.. _add your repo: https://coveralls.io/repos/new
