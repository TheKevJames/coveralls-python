"""Tests for handling malformed git remote output."""
import os
import unittest.mock
from coveralls.git import git_info


class MalformedRemoteTest(unittest.TestCase):
    @unittest.mock.patch('coveralls.git.run_command')
    @unittest.mock.patch.dict(
        os.environ,
        {'GITHUB_ACTIONS': 'true', 'GITHUB_REF': 'refs/heads/main'},
        clear=True,
    )
    def test_git_info_handles_malformed_remote_fetch_line(self, mock_run_command):
        """
        Regression test: git remote -v can output malformed lines containing
        '(fetch)' that have fewer than 2 space-separated tokens.  The parser
        must skip these gracefully instead of raising an IndexError.
        """
        def run_side_effect(*args):
            if args == ('git', 'remote', '-v'):
                # Simulate a malformed remote line followed by a valid one
                return '(fetch)\norigin  https://github.com/user/repo.git (fetch)\n'
            if args == ('git', '--no-pager', 'log', '-1', '--pretty=format:%H'):
                return 'abc123'
            if args == ('git', '--no-pager', 'log', '-1', '--pretty=format:%aN'):
                return 'Test Author'
            if args == ('git', '--no-pager', 'log', '-1', '--pretty=format:%ae'):
                return 'test@example.com'
            if args == ('git', '--no-pager', 'log', '-1', '--pretty=format:%cN'):
                return 'Test Committer'
            if args == ('git', '--no-pager', 'log', '-1', '--pretty=format:%ce'):
                return 'committer@example.com'
            if args == ('git', '--no-pager', 'log', '-1', '--pretty=format:%s'):
                return 'test commit'
            raise AssertionError(f'Unexpected git command: {args}')

        mock_run_command.side_effect = run_side_effect

        # This should NOT raise an IndexError
        result = git_info()

        # The malformed line should be skipped; only the valid remote should appear
        assert result['git']['remotes'] == [{
            'name': 'origin',
            'url': 'https://github.com/user/repo.git',
        }]
