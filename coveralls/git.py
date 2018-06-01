import logging
import os
import subprocess

from .exception import CoverallsException


log = logging.getLogger(__name__)


def run_command(*args):
    cmd = subprocess.Popen(list(args), stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    stdout, stderr = cmd.communicate()

    if cmd.returncode != 0:
        raise CoverallsException(
            'command return code {}, STDOUT: "{}"\nSTDERR: "{}"'.format(
                cmd.returncode, stdout, stderr))

    try:
        return stdout.decode().strip()
    except UnicodeDecodeError:
        return stdout.decode('utf-8').strip()



def gitlog(fmt):
    glog = run_command('git', '--no-pager', 'log', '-1',
                       '--pretty=format:{}'.format(fmt))

    try:
        return str(glog)
    except UnicodeEncodeError:
        return unicode(glog)  # pylint: disable=undefined-variable


def git_info():
    """ A hash of Git data that can be used to display more information to
        users.

        Example:
        "git": {
            "head": {
                "id": "5e837ce92220be64821128a70f6093f836dd2c05",
                "author_name": "Wil Gieseler",
                "author_email": "wil@example.com",
                "committer_name": "Wil Gieseler",
                "committer_email": "wil@example.com",
                "message": "depend on simplecov >= 0.7"
            },
            "branch": "master",
            "remotes": [{
                "name": "origin",
                "url": "https://github.com/lemurheavy/coveralls-ruby.git"
            }]
        }
    """
    try:
        branch = (os.environ.get('APPVEYOR_REPO_BRANCH') or
                  os.environ.get('BUILDKITE_BRANCH') or
                  os.environ.get('CI_BRANCH') or
                  os.environ.get('CIRCLE_BRANCH') or
                  os.environ.get('GIT_BRANCH') or
                  os.environ.get('TRAVIS_BRANCH') or
                  run_command('git', 'rev-parse', '--abbrev-ref', 'HEAD'))
        head = {
            'id': gitlog('%H'),
            'author_name': gitlog('%aN'),
            'author_email': gitlog('%ae'),
            'committer_name': gitlog('%cN'),
            'committer_email': gitlog('%ce'),
            'message': gitlog('%s'),
        }
        remotes = [{'name': line.split()[0], 'url': line.split()[1]}
                   for line in run_command('git', 'remote', '-v').splitlines()
                   if '(fetch)' in line]

        return {
            'git': {
                'branch': branch,
                'head': head,
                'remotes': remotes,
            },
        }
    except CoverallsException as ex:
        log.warning('Failed collecting git data. Are you running '
                    'coveralls inside a git repository?', exc_info=ex)
        return {}
