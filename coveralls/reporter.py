# coding: utf-8
import logging
import os
import sys

from coverage import __version__
from coverage.misc import NoSource
from coverage.misc import NotPython
from coverage.phystokens import source_encoding

from .exception import CoverallsException


log = logging.getLogger('coveralls.reporter')


class CoverallReporter(object):
    """Custom coverage.py reporter for coveralls.io"""

    def __init__(self, cov, conf):
        self.coverage = []
        self.report(cov, conf)

    def report5(self, cov):
        # N.B. this method is 99% copied from the coverage source code;
        # unfortunately, the coverage v5 style of `get_analysis_to_report`
        # errors out entirely if any source file has issues -- which would be a
        # breaking change for us. In the interest of backwards compatibility,
        # I've copied their code here so we can maintain the same `coveralls`
        # API regardless of which `coverage` version is being used.
        #
        # TODO: deprecate the relevant APIs so we can just use the coverage
        # public API directly.
        #
        # from coverage.report import get_analysis_to_report
        # try:
        #     for cu, analyzed in get_analysis_to_report(cov, None):
        #         self.parse_file(cu, analyzed)
        # except NoSource:
        #     # Note that this behavior must necessarily change between
        #     # coverage<5 and coverage>=5, as we are no longer interweaving
        #     # with get_analysis_to_report (a single exception breaks the
        #     # whole loop)
        #     log.warning('No source for at least one file')
        # except NotPython:
        #     # Note that this behavior must necessarily change between
        #     # coverage<5 and coverage>=5, as we are no longer interweaving
        #     # with get_analysis_to_report (a single exception breaks the
        #     # whole loop)
        #     log.warning('A source file is not python')
        # except CoverageException as e:
        #     if str(e) != 'No data to report.':
        #         raise

        from coverage.files import FnmatchMatcher, prep_patterns

        # get_analysis_to_report starts here; changes marked with TODOs
        file_reporters = cov._get_file_reporters(None)  # pylint: disable=W0212
        config = cov.config

        if config.report_include:
            matcher = FnmatchMatcher(prep_patterns(config.report_include))
            file_reporters = [fr for fr in file_reporters
                              if matcher.match(fr.filename)]

        if config.report_omit:
            matcher = FnmatchMatcher(prep_patterns(config.report_omit))
            file_reporters = [fr for fr in file_reporters
                              if not matcher.match(fr.filename)]

        # TODO: deprecate changes
        # if not file_reporters:
        #     raise CoverageException("No data to report.")

        for fr in sorted(file_reporters):
            try:
                analysis = cov._analyze(fr)  # pylint: disable=W0212
            except NoSource:
                if not config.ignore_errors:
                    # TODO: deprecate changes
                    # raise
                    log.warning('No source for %s', fr.filename)
            except NotPython:
                # Only report errors for .py files, and only if we didn't
                # explicitly suppress those errors.
                # NotPython is only raised by PythonFileReporter, which has a
                # should_be_python() method.
                if fr.should_be_python():
                    if config.ignore_errors:
                        msg = "Couldn't parse Python file '{}'".format(
                            fr.filename)
                        cov._warn(msg,  # pylint: disable=W0212
                                  slug="couldnt-parse")
                    else:
                        # TODO: deprecate changes
                        # raise
                        log.warning('Source file is not python %s',
                                    fr.filename)
            else:
                # TODO: deprecate changes (well, this one is fine /shrug)
                # yield (fr, analysis)
                self.parse_file(fr, analysis)

    def report(self, cov, conf, morfs=None):
        """
        Generate a part of json report for coveralls

        `morfs` is a list of modules or filenames.
        `outfile` is a file object to write the json to.
        """
        # pylint: disable=too-many-branches
        try:
            from coverage.report import Reporter
            self.reporter = Reporter(cov, conf)
        except ImportError:  # coverage >= 5.0
            return self.report5(cov)

        units = None
        if hasattr(self.reporter, 'find_code_units'):
            self.reporter.find_code_units(morfs)
        else:
            units = self.reporter.find_file_reporters(morfs)

        if units is None:
            if hasattr(self.reporter, 'code_units'):
                units = self.reporter.code_units
            else:
                units = self.reporter.file_reporters

        for cu in units:
            try:
                _fn = self.reporter.coverage._analyze  # pylint: disable=W0212
                analyzed = _fn(cu)
                self.parse_file(cu, analyzed)
            except NoSource:
                if not self.reporter.config.ignore_errors:
                    log.warning('No source for %s', cu.filename)
            except NotPython:
                # Only report errors for .py files, and only if we didn't
                # explicitly suppress those errors.
                if (cu.should_be_python()
                        and not self.reporter.config.ignore_errors):
                    log.warning('Source file is not python %s', cu.filename)
            except KeyError:
                version = [int(x) for x in __version__.split('.')]
                cov3x = version[0] < 4
                cov40 = version[0] == 4 and version[1] < 1
                if cov3x or cov40:
                    raise CoverallsException(
                        'Old (<4.1) versions of coverage.py do not work '
                        'consistently on new versions of Python. Please '
                        'upgrade your coverage.py.'
                    )

                raise

        return self.coverage

    @staticmethod
    def get_hits(line_num, analysis):
        """
        Source file stats for each line.

        * A positive integer if the line is covered, representing the number
          of times the line is hit during the test suite.
        * 0 if the line is not covered by the test suite.
        * null to indicate the line is not relevant to code coverage (it may
          be whitespace or a comment).
        """
        if line_num in analysis.missing:
            return 0

        if line_num not in analysis.statements:
            return None

        return 1

    @staticmethod
    def get_arcs(analysis):
        """
        Hit stats for each branch.

        Returns a flat list where every four values represent a branch:
        1. line-number
        2. block-number (not used)
        3. branch-number
        4. hits (we only get 1/0 from coverage.py)
        """
        if not analysis.has_arcs():
            return None

        if not hasattr(analysis, 'branch_lines'):
            # N.B. switching to the public method analysis.missing_branch_arcs
            # would work for half of what we need, but there doesn't seem to be
            # an equivalent analysis.executed_branch_arcs
            branch_lines = analysis._branch_lines()  # pylint: disable=W0212
        else:
            branch_lines = analysis.branch_lines()

        branches = []

        for l1, l2 in analysis.arcs_executed():
            if l1 in branch_lines:
                branches.extend((l1, 0, abs(l2), 1))

        for l1, l2 in analysis.arcs_missing():
            if l1 in branch_lines:
                branches.extend((l1, 0, abs(l2), 0))

        return branches

    def parse_file(self, cu, analysis):
        """Generate data for single file"""
        if hasattr(analysis, 'parser'):
            filename = cu.file_locator.relative_filename(cu.filename)
            source_lines = analysis.parser.lines
            with cu.source_file() as source_file:
                source = source_file.read()

            try:
                if sys.version_info < (3, 0):
                    encoding = source_encoding(source)
                    if encoding != 'utf-8':
                        source = source.decode(encoding).encode('utf-8')
            except UnicodeDecodeError:
                log.warning(
                    'Source file %s can not be properly decoded, skipping. '
                    'Please check if encoding declaration is ok',
                    os.path.basename(cu.filename))
                return
        else:
            if hasattr(cu, 'relative_filename'):
                filename = cu.relative_filename()
            else:
                filename = analysis.coverage.file_locator.relative_filename(
                    cu.filename)

            token_lines = analysis.file_reporter.source_token_lines()
            source_lines = list(enumerate(token_lines))
            source = analysis.file_reporter.source()

        coverage_lines = [self.get_hits(i, analysis)
                          for i in range(1, len(source_lines) + 1)]

        # ensure results are properly merged between platforms
        posix_filename = filename.replace(os.path.sep, '/')

        results = {
            'name': posix_filename,
            'source': source,
            'coverage': coverage_lines,
        }

        branches = self.get_arcs(analysis)
        if branches:
            results['branches'] = branches

        self.coverage.append(results)
