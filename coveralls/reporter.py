# coding: utf-8
from coverage.report import Reporter


class CoverallReporter(Reporter):
    """ Custom coverage.py reporter for coveralls.io
    """
    def report(self, morfs=None):
        """ Generate a part of json report for coveralls

        `morfs` is a list of modules or filenames.
        `outfile` is a file object to write the json to.
        """
        self.source_files = []
        self.report_files(self.parse_file, morfs)
        return self.source_files

    def get_hits(self, line_num, analysis):
        """ Source file stats for each line.

            * A positive integer if the line is covered,
            representing the number of times the line is hit during the test suite.
            * 0 if the line is not covered by the test suite.
            * null to indicate the line is not relevant to code coverage
              (it may be whitespace or a comment).
        """
        if line_num in analysis.missing:
            return 0
        if line_num in analysis.statements:
            return 1
        return None

    def parse_file(self, cu, analysis):
        """ Generate data for single file """
        filename = cu.file_locator.relative_filename(cu.filename)
        coverage_lines = [self.get_hits(i, analysis) for i in xrange(1, len(analysis.parser.lines) + 1)]
        self.source_files.append({
            'name': filename,
            'source': cu.source_file().read(),
            'coverage': coverage_lines
        })