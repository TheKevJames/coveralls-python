import logging
import pathlib
from typing import Any

import coverage
from coverage.plugin import FileReporter
from coverage.results import Analysis

try:
    # coverage v7.5+ moved get_analysis_to_report into report_core
    from coverage.report_core import get_analysis_to_report
except ImportError:
    from coverage.report import (  # type: ignore[attr-defined]
        get_analysis_to_report,
    )


log = logging.getLogger('coveralls.reporter')


class CoverallReporter:
    """Custom coverage.py reporter for coveralls.io."""

    def __init__(
            self,
            cov: coverage.Coverage,
            base_dir: str = '',
            src_dir: str = '',
    ) -> None:
        self.base_dir = self.sanitize_dir(base_dir)
        self.src_dir = self.sanitize_dir(src_dir)

        self.coverage: list[dict[str, Any]] = []
        self.report(cov)

    @staticmethod
    def sanitize_dir(directory: str) -> str:
        if directory:
            directory = pathlib.PurePath(directory).as_posix()
            if directory[-1] != '/':
                directory += '/'
        return directory

    def report(self, cov: coverage.Coverage) -> None:
        try:
            for (fr, analysis) in get_analysis_to_report(cov, None):
                self.parse_file(fr, analysis)
        except coverage.exceptions.NoDataError:
            return
        except Exception as e:
            raise RuntimeError(f'Got coverage library error: {e}') from e

    @staticmethod
    def get_hits(line_num: int, analysis: Analysis) -> int | None:
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
    def get_arcs(analysis: Analysis) -> list[int]:
        """
        Hit stats for each branch.

        Returns a flat list where every four values represent a branch:
        1. line-number
        2. block-number (not used)
        3. branch-number
        4. hits (we only get 1/0 from coverage.py)
        """
        has_arcs: bool
        try:
            has_arcs = analysis.has_arcs()  # type: ignore[operator]
        except TypeError:
            # coverage v7.5+
            has_arcs = analysis.has_arcs

        if not has_arcs:
            return []

        missing_arcs: dict[int, list[int]] = analysis.missing_branch_arcs()
        executed_arcs = analysis.executed_branch_arcs()

        branches: list[int] = []
        for l1, l2s in executed_arcs.items():
            for l2 in l2s:
                branches.extend((l1, 0, abs(l2), 1))
        for l1, l2s in missing_arcs.items():
            for l2 in l2s:
                branches.extend((l1, 0, abs(l2), 0))

        return branches

    def parse_file(self, cu: FileReporter, analysis: Analysis) -> None:
        """Generate data for single file."""
        # ensure results are properly merged between platforms
        posix_filename = pathlib.PurePath(cu.relative_filename()).as_posix()
        if self.base_dir and posix_filename.startswith(self.base_dir):
            posix_filename = posix_filename[len(self.base_dir):]
        posix_filename = self.src_dir + posix_filename

        token_lines = cu.source_token_lines()
        coverage_lines = [
            self.get_hits(i, analysis)
            for i, _ in enumerate(token_lines, 1)
        ]

        results = {
            'name': posix_filename,
            'source': cu.source(),
            'coverage': coverage_lines,
        }

        branches = self.get_arcs(analysis)
        if branches:
            results['branches'] = branches

        self.coverage.append(results)
