Changelog
---------

0.4.2 (2014-05-05)
~~~~~~~~~~~~~~~~~~
* Handle 503 errors from coveralls.io

0.4.1 (2014-01-15)
~~~~~~~~~~~~~~~~~~
* Fix gitlog output with utf8

0.4 (2013-12-27)
~~~~~~~~~~~~~~~~
* Added support for --rcfile=<file> option to cli
* Improved docs: nosetests and troubleshooting sections added
* Added debug in case of UnicodeDecodeError
* Removed sh dependency in favor of Windows compatibility

0.3 (2013-10-02)
~~~~~~~~~~~~~~~~
* Added initial support for Circle CI
* Fixed Unicode not defined error in python 3

0.2 (2013-05-26)
~~~~~~~~~~~~~~~~
* Python 3.2 and PyPy support
* Graceful handling of coverage exceptions
* Fixed UnicodeDecodeError in json encoding
* Improved readme

0.1.1 (2013-02-13)
~~~~~~~~~~~~~~~~~~
* Introduced COVERALLS_REPO_TOKEN environment variable as a fallback for Travis
* Removed repo_token from verbose output for security reasons

0.1 (2013-02-12)
~~~~~~~~~~~~~~~~
* Initial release
