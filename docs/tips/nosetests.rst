Nosetests
=========

`Nosetests`_ provide a plugin for coverage measurement of your code::

    $ nosetests  --with-coverage --cover-package=<your_package_name>

However, nosetests gathers coverage for all executed code, ignoring the ``source`` config option in ``.coveragerc``.

This well make ``coveralls`` report unnecessary files, which can be inconvenient. To workaround this issue, you can use the ``omit`` option in your ``.coveragerc`` to specify a list of filename patterns to leave out of reporting.

For example::

    [report]
    omit =
        */venv/*
        */my_project/ignorable_file.py
        */test_script.py

Note, that native ``coverage.py`` and ``py.test`` are not affected by this problem and do not require this workaround.

.. _Nosetests: http://nose.readthedocs.org/en/latest/plugins/cover.html
