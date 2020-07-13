.. _multilang:

Multiple Language Support
=========================

Tracking multi-language repo coverage requires an extra setup of merging coverage data for submission.

To send coveralls.io merged data, you must use each of your coverage reporting tools in sequence, then merge the JSON data in the last step.

For example, to submit coverage for a project using both ``mocha`` and ``py.test``, you could use the `coveralls-lcov`_ library and run::

    # generate mocha coverage data
    mocha --reporter mocha-lcov-reporter */tests/static/js/* > coverage.info

    # convert data with coveralls-lcov
    coveralls-lcov -v -n coverage.info > coverage.json

    # merge mocha coverage with python coverage and send to coveralls
    coveralls --merge=coverage.json

If you want to use this library to create a JSON blob for usage elsewhere, you can run::

    coveralls --output=coverage.json

Technical Details
-----------------

The JSON file to be merged must be of "coveralls-style" and contain thus a ``source_files`` key. The `Coveralls API`_ has more information.

.. _coveralls-lcov: https://github.com/okkez/coveralls-lcov
.. _Coveralls API: https://docs.coveralls.io/api-introduction
