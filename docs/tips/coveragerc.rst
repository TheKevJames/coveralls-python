Tips for .coveragerc
====================

This section is a list of most common options for ``coverage.py``, which collects all the coverage information. Coveralls is populated from this data, so it's good to know `how to to configure coverage.py`_.

To limit the `report to only your packages`_, specify their names (or directories)::

    [run]
    source = pkgname,your_otherpackage

To exclude parts of your source from coverage, for example migrations folders::

    [report]
    omit = */migrations/*

Some lines are never executed in your tests, but that can be ok.
To mark those lines use inline comments right in your source code::

    if debug:   # pragma: no cover
        msg = "blah blah"
        log_message(msg, a)

Sometimes it can be tedious to mark them in code, so you can `specify whole lines in .coveragerc`_::

    [report]
    exclude_lines =
        pragma: no cover
        def __repr__
        raise AssertionError
        raise NotImplementedError
        if __name__ == .__main__.:

Finally, if you're using non-default configuration file, you can specify it in the coveralls command::

    $ coveralls --rcfile=<file>

.. _how to to configure coverage.py: http://coverage.readthedocs.io/en/latest/config.html
.. _report to only your packages: http://coverage.readthedocs.io/en/latest/source.html
.. _specify whole lines in .coveragerc: http://coverage.readthedocs.io/en/latest/excluding.html
