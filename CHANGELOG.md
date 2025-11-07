<a name="4.0.2"></a>
## 4.0.2 (2025-11-07)

#### Internal

* update python support: drop EOL'd versions (3.8, 3.9), begin testing on new versions (3.13, 3.14), and mark explicit future compatibility up to <4.0

<a name="4.0.1"></a>
## 4.0.1 (2024-05-15)

#### Internal

* support ``coverage`` v7.5+ (#442) ([f41dca5](f41dca5))
* skip tests which require running in a git repo when ``.git`` is missing (#443) ([b566fc3](b566fc3))

<a name="4.0.0"></a>
## 4.0.0 (2024-04-29)

#### BREAKING CHANGES

When ``config.ignore_errors`` is Falsey, failures to parse Python files or
look up file sources will now interrupt and early exit collection, which
matches default ``coverage`` behaviour. Previously, we had manually muted
these errors and/or only errored after collecting multiple failures.

[See the coverage.py docs](https://coverage.readthedocs.io/en/7.5.1/config.html#report-ignore-errors) for setting this option.

#### Features

* support ``pyproject.toml`` packages by default (via ``coverage[toml]``) ([962e2242](962e2242))
* add ``python-coveralls`` entrypoint ([3d8d56e4](3d8d56e4))

#### Bug Fixes

* fixup default support for Github Actions (#427, #385) ([44e95634](44e95634)) -- thanks @andy-maier
* fail and report on *all* errors, not just those derived from ``CoverallsException`` ([be446287](be446287))

#### Internal

* support ``coverage`` v7.0 - v7.4 ([8fb36645](8fb36645))
* support Python 3.11 and 3.12 ([8dbce919](8dbce919))
* fixup docs for tox v3 and v4 support (#371) ([05bb20d8](05bb20d8)) -- thanks @masonf
* drop support for Python3.7 and below
* drop support for ``coverage`` v4.x ([752f52a0](752f52a0))
* auto-build and publish ``docker`` images
* refactor: more closely match ``coverage`` public interface (#421)

<a name="3.3.1"></a>
## 3.3.1 (2021-11-11)

#### Bug Fixes

* correctly support parallel execution on CircleCI (#336) ([2610885a](2610885a))

#### Internal

* exclude a few incompatible `coverage` versions (#337)

`coverage` versions v6.0.0 through v6.1.1 exhibited some incompatibilies with
`coveralls`; we've updated our version compatibility ranges to exclude those
versions.

<a name="3.3.0"></a>
## 3.3.0 (2021-11-04)

#### Features

* **cli:**  add --srcdir option (#306) ([4120c540](4120c540))
* **deps:**  add support for coverage v6.x (#330) ([372443dc](372443dc), closes [#326](326))

Note this implicitly improves support for Python 3.10, as coverage v6.x includes some fixes for v3.10 of Python.

#### Bug Fixes

* **env:**  fixup handling of default env service values (#314) ([1a0fd9b3](1a0fd9b3), closes [#303](303))

This solves some edge cases around duplicated / unmerged coverage results in parallel runs.

<a name="3.2.0"></a>
## 3.2.0 (2021-07-20)

#### Features

* **api:**  support officially documented generic CI env vars (#300) ([ca1c6a47](ca1c6a47))

<a name="3.1.0"></a>
## 3.1.0 (2021-05-24)

#### Features

* **cli**:  add `--basedir` and `--submit` options (#287) ([165a5cd1](165a5cd1))
* **github:**  push coverage info from tags (#284) ([0a49bd28](0a49bd28))

<a name="3.0.1"></a>
## 3.0.1 (2021-03-02)

#### Bug Fixes

* **github:**  send null job_id to fix 422 during resubmission (#269) ([54be7545](54be7545))

<a name="3.0.0"></a>
## 3.0.0 (2021-01-12)

#### Features (BREAKING)

* **config:**  reorder configuration precedence (#249) ([f4faa92d](f4faa92d))

We have *reversed* the order in which configurations are parsed. This means we
are now following the following precedence (latest configured value is used):

1. CI Config
2. COVERALLS_* env vars
3. .coveralls.yml file
4. CLI flags

If you have the same fields set in multiple of the above locations, please
double-check them before upgrading to v3.

The motivation for this change is allowing users to selectively fix values
which may be automatically set to the wrong value. For example, Github Actions
users may find that Github Actions expects you to use a different "service name"
in various different cases. Now you can run, for example:

   coveralls --service=github

In places where you need to override the default (which is `github-actions`).

#### Bug Fixes

* **github:**  send null job_id to fix 422 ([05b66aa0](05b66aa0))
* **api:**  fixup retries for services without job IDs ([6ebdc5e2](6ebdc5e2))

<a name="2.2.0"></a>
## 2.2.0 (2020-11-20)

#### Features

* **api:**  add workaround allowing job resubmission (#241) ([0de0c019](0de0c019))

#### Bug Fixes

* **integrations:**  fixup environment detection for Semaphore CI (#236) ([ad4f8fa8](ad4f8fa8))

<a name="2.1.2"></a>
## 2.1.2 (2020-08-12)

#### Features

* **circleci:**  support parallel builds (#233) ([5e05654c](5e05654c))
             Note: this is partially a fix for the `--finish` command
             introduced in v2.1.0, which did not seem to work for some CircleCI
             users.


<a name="2.1.1"></a>
## 2.1.1 (2020-07-08)

#### Bug Fixes

*  fix unhashable CoverallsException (#230) ([aa55335d](aa55335d))
   This fixes a regression introduced in v2.1.0 which affected (at least) any
   Python 3.5 installations.


<a name="2.1.0"></a>
## 2.1.0 (2020-07-07)

#### Features

* **cli**:  add new `--finish` flag for finalizing parallel builds (#277) ([f597109b](f597109b))

#### Bug Fixes

* **github:**  fix Github Actions support (#227) ([f597109b](f597109b))

<a name="2.0.0"></a>
## 2.0.0 (2020-04-07)

#### Compatiblity (BREAKING CHANGES)

*  We have now dropped support for End-Of-Life'd versions of Python and
   particularly old versions of the `coverage` library; if you are still using
   Python v2.7 or v3.4, or you are using `coverage<4.1`, this library will no
   longer be compatible starting from this release -- please pin to
   `coveralls<2.0.0`.

<a name="1.11.1"></a>
## 1.11.1 (2020-02-15)

#### Bug Fixes

* **github:**  rename to github-actions ([9e65a059](9e65a059))
    This fixes a regression introduced with v1.11.0, which may have prevented
    usage of this library on Github Actions.

<a name="1.11.0"></a>
## 1.11.0 (2020-02-12)

#### Fixes

* **github:**  add `service_number` for github actions ([9f93bd8e](9f93bd8e))
    This should fix support for parallel builds.

#### Compatibility

*  Python 2.7 and 3.4 are now officially End-Of-Life'd. Consider them deprecated
   from the perspective of this package -- we'll remove them in an upcoming
   release (likely the first one which requires non-trivial work to continue
   supporting them!).

<a name="1.10.0"></a>
## 1.10.0 (2019-12-31)

#### Features

*  support coverage>=5.0 (#214) ([4a917402](4a917402))

<a name="1.9.2"></a>
## 1.9.2 (2019-12-03)

#### Bug Fixes

* **github:**  fixup incorrect API usage (#209) ([c338cab4](c338cab4))

<a name="1.9.1"></a>
## 1.9.1 (2019-12-03)

#### Compatibility

*  this release marks Python 3.8 as officially supported. Earlier versions probably
   supported Python 3.8 too, but now we're *sure*.

<a name="1.9.0"></a>
## 1.9.0 (2019-12-03)

#### Features

* **support:**  support Github Actions CI (#207) ([817119c3](817119c3))

#### Bug Fixes

* **compatibility:**  fixup coverage.__version__ comparisons (#208) ([03a57a9a](03a57a9a))

<a name="1.8.2"></a>
## 1.8.2 (2019-07-29)

### Internal

* **dependencies**: update pass urllib3<1.25 pin, now that that's fixed.

<a name="1.8.1"></a>
## 1.8.1 (2019-06-16)

#### Bug Fixes

* **dependencies:**  pin `coverage` to `< 5.0`, since the current `5.0` alphas are
                     introducing breaking changes. Once `5.0` is stable, we'll
                     remove the pin.

<a name="1.8.0"></a>
## 1.8.0 (2019-06-02)

#### Features

* **flag:**  allow disabling SSL verification ([2e3b5c61](2e3b5c61))

#### Bug Fixes

* **git:**  fix support for case where git binary is missing ([5bbceaae](5bbceaae))

<a name="1.7.0"></a>
## 1.7.0 (2019-03-20)

#### Features

* **api:**  support pull requests on buildkite (#197) ([2700e3e2](2700e3e2))

#### Bug Fixes

* **cli:**  ensure upload failures trigger cli failures ([16192b84](16192b84))

<a name="1.6.0"></a>
## 1.6.0 (2019-02-18)

#### Features

* **support:**  add support for SemaphoreCI (#193) ([4e09918a](4e09918a))

<a name="1.5.1"></a>
## 1.5.1 (2018-09-28)

#### Features
* **git:**  omit git info when git isn't installed (#187) ([764956ea](764956ea))
  * ... instead of erroring. The fixes the v1.4.0 release of "supporting
    non-git repos" when the git binary is not installed.
  * Note that commit info can still be set with env vars, even in non-git
    repositories -- see the docs for more info!

#### Compatibility
* **python:**  include python 3.7 in matrix tests ([023d474](023d474))
  * previous versions of `coveralls-python` should be compatible with Python 3.7, no
    code changes were required to make tests pass

#### Internal
* remove `pytest-runner` as a dependency (#185) ([4cbbfcd](4cbbfcd))

<a name="1.5.0"></a>
## 1.5.0 (2018-08-31)

#### Features
* **cli:**  allow execution as a module (#184) ([b261a853](b261a853), closes [#183](183))

#### Bug Fixes
* **paths:**  ensure windows paths are normalized to posix ([661e0f54](661e0f54), closes [#153](153))

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
* **cli:**  allow `service_name` override from cli flag or env var (#167) ([e8a98904](e8a98904))
* **coveralls-enterprise:**  add support for coveralls enterprise (#166) ([7383f377](7383f377))
* **git:**  silently omit git data when git is unavailable (#176) ([f9db83cd](f9db83cd))
* **jenkins:**
  *  add logic to parse `CI_PULL_REQUEST` env variable (#171) ([34a037f5](34a037f5))
  *  add support for jenkins (#160) ([4e8cd9ec](4e8cd9ec))

<a name="1.2.0"></a>
### 1.2.0 (2017-08-15)

#### Features
* **support:**  add support for AppVeyor CI ([1a62ce27](1a62ce27))
* **support:**  add support for BuildKite CI ([a58d6f9e](a58d6f9e))
* **support:**  add support for branch coverage ([e2413e38](e2413e38))
* **support:**  add support for parallel builds in Coveralls CI ([7ba3a589](7ba3a589))

#### Bug Fixes
* fix coverage count in cases of partial branch coverage ([b9ab7037](b9ab7037))
* fix SNI validation errors in python2 ([c5541263](c5541263))
* warn when PyYAML is missing ([711e9e4c](711e9e4c))

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
*  codeship experimetal support (`CI_BRANCH` env variable)
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
*  **Backwards Incompatible**: make pyyaml optional. If you're using .coveralls.yml, make sure to install `coveralls[yaml]`
*  coverage 4 alpha support
*  allow debug and output options to work without `repo_token`
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
*  introduced `COVERALLS_REPO_TOKEN` environment variable as a fallback for Travis
*  removed `repo_token` from verbose output for security reasons

<a name="0.1"></a>
### 0.1 (2013-02-12)

#### Features
*  initial release
