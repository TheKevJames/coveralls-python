<a name="1.4.0"></a>
## 1.4.0 (2018-08-24)


#### Performance

* **git:**  call fallback git commands in fallback cases only ([e42095b4](e42095b4))

#### Features

* **env:**  support git env vars (#182) ([a1918e89](a1918e89))
  * This change also adds support for non-git repos.
* **flags:**  add ability to add named job (#181) ([f7ba07bf](f7ba07bf))

#### Compatibility

* **python:**  drop support for Python 3.3 ([dcb06fc1](dcb06fc1))


<a name="1.3.0"></a>
## 1.3.0 (2018-03-02)


#### Features

* **ci:**  add Travis PR support (#162) ([baf683ee](baf683ee))
* **cli:**  allow service_name override from cli flag or env var (#167) ([e8a98904](e8a98904))
* **coveralls-enterprise:**  add support for coveralls enterprise (#166) ([7383f377](7383f377))
* **git:**  silently omit git data when git is unavailable (#176) ([f9db83cd](f9db83cd))
* **jenkins:**
  *  add logic to parse CI_PULL_REQUEST env variable (#171) ([34a037f5](34a037f5))
  *  add support for jenkins (#160) ([4e8cd9ec](4e8cd9ec))



<a name="1.2.0"></a>
### 1.2.0 (2017-08-15)


#### Features

*   add support for AppVeyor CI ([1a62ce27](https://github.com/coveralls-clients/coveralls-python/commit/1a62ce2706ac73a521d231990e043886627bbf89))
*   add support for BuildKite CI ([a58d6f9e](https://github.com/coveralls-clients/coveralls-python/commit/a58d6f9e3c00ad087ce2b516e1b1c175357b6abe))
*   add support for branch coverage ([e2413e38](https://github.com/coveralls-clients/coveralls-python/commit/e2413e385b20bb92b1f4f9395f22fec37632d15b))
*   add support for parallel builds in Coveralls CI ([7ba3a589](https://github.com/coveralls-clients/coveralls-python/commit/7ba3a5894dae8b635e9e75b6d2ac241aae9d4597))

#### Bug Fixes

*   fix coverage count in cases of partial branch coverage ([b9ab7037](https://github.com/coveralls-clients/coveralls-python/commit/b9ab703732af9ebd25f7ab937543b35ac57dac5e))
*   fix SNI validation errors in python2 ([c5541263](https://github.com/coveralls-clients/coveralls-python/commit/c5541263a220ff4347244d1aa70e409be115ae01))
*   warn when PyYAML is missing ([711e9e4c](https://github.com/coveralls-clients/coveralls-python/commit/711e9e4c3bc44a88ec51216b20573119e90f449f))



<a name="1.1"></a>
### 1.1 (2015-10-04)


#### Features
*   support for Circle CI



<a name="1.0"></a>
### 1.0 (2015-09-17)


#### Features
*   official coverage 4.0 support



<a name="1.0b1"></a>
### 1.0 (2015-08-14)


#### Features
*  coverage 4 beta support
*  codeship experimetal support (CI_BRANCH env variable)
*  drop python 3.2 support (as coverage 4 does not support it)
*  repo token usage is deprecated (but still supported) in favor of env variable.
*  error reporting is improved, exist status codes added



<a name="1.0a2"></a>
### 1.0a2 (2015-02-19)


#### Features
*  fix latest alpha coverage.py support
*  remove erroneous warning message when writing output to a file



<a name="1.0a1"></a>
### 1.0a1 (2015-02-19)


#### Features
*  **Backwards Incompatible**: make pyyaml optional. If you're using .coveralls.yml, make sure to install coveralls[yaml]
*  coverage 4 alpha support
*  allow debug and output options to work without repo_token
*  fix merge command for python 3.X



<a name="0.5"></a>
### 0.5 (2014-12-10)


#### Features
*  add option --output=<file> for saving json to file for possible merging with coverages from other languages
*  add merge command for sending coverage stats from multiple languages



<a name="0.4.4"></a>
### 0.4.4 (2014-09-28)


#### Features
*  proper fix coverage.py dependency version



<a name="0.4.3"></a>
### 0.4.3 (2014-09-28)


#### Features
*  fix coverage.py dependency version



<a name="0.4.2"></a>
### 0.4.2 (2014-05-05)


#### Features
*  handle 503 errors from coveralls.io



<a name="0.4.1"></a>
### 0.4.1 (2014-01-15)


#### Features
*  fix gitlog output with utf8



<a name="0.4"></a>
### 0.4 (2013-12-27)


#### Features
*  added support for --rcfile=<file> option to cli
*  improved docs: nosetests and troubleshooting sections added
*  added debug in case of UnicodeDecodeError
*  removed sh dependency in favor of Windows compatibility



<a name="0.3"></a>
### 0.3 (2013-10-02)


#### Features
*  added initial support for Circle CI
*  fixed Unicode not defined error in python 3



<a name="0.2"></a>
### 0.2 (2013-05-26)


#### Features
*  Python 3.2 and PyPy support
*  graceful handling of coverage exceptions
*  fixed UnicodeDecodeError in json encoding
*  improved readme



<a name="0.1.1"></a>
### 0.1.1 (2013-02-13)


#### Features
*  introduced COVERALLS_REPO_TOKEN environment variable as a fallback for Travis
*  removed repo_token from verbose output for security reasons



<a name="0.1"></a>
### 0.1 (2013-02-12)


#### Features
*  initial release
