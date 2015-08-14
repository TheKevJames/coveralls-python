Changelog
---------

1.0b1 (2015-08-14)
~~~~~~~~~~~~~~~~~~
* Coverage 4 beta support
* Codeship experimetal support (CI_BRANCH env variable)
* Drop python 3.2 support (as coverage 4 does not support it)
* Repo token usage is deprecated (but still supported) in favor of env variable.
* Error reporting is improved, exist status codes added

1.0a2 (2015-02-19)
~~~~~~~~~~~~~~~~~~
* Fix latest alpha coverage.py support
* Remove erroneous warning message when writing output to a file

1.0a1 (2015-02-19)
~~~~~~~~~~~~~~~~~~
* **Backwards incompatible**: make pyyaml optional. If you're using .coveralls.yml, make sure to install coveralls[yaml]
* Coverage 4 alpha support
* Allow debug and output options to work without repo_token
* Fix merge command for python 3.X

0.5 (2014-12-10)
~~~~~~~~~~~~~~~~
* Add option --output=<file> for saving json to file for possible merging with coverages from other languages
* Add merge command for sending coverage stats from multiple languages

0.4.4 (2014-09-28)
~~~~~~~~~~~~~~~~~~
* Proper fix coverage.py dependency version

0.4.3 (2014-09-28)
~~~~~~~~~~~~~~~~~~
* Fix coverage.py dependency version

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
