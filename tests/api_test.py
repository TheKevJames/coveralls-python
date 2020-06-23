import json
import os

import mock

from coveralls import Coveralls


@mock.patch.dict(os.environ, {}, clear=True)
def test_output_to_file(tmpdir):
    """Check we can write coveralls report into the file."""
    test_log = tmpdir.join('test.log')
    Coveralls(repo_token='xxx').save_report(test_log.strpath)
    report = test_log.read()

    assert json.loads(report)['repo_token'] == 'xxx'


@mock.patch.dict(os.environ, {}, clear=True)
def test_load_config_from_github():
    """Check getting config from GH actions works when not in a PR."""
    os.environ['GITHUB_RUN_ID'] = 'run_id'
    os.environ['GITHUB_REF'] = 'refs/push/somehash'
    assert Coveralls.load_config_from_github() == (
        'github-actions', 'run_id', None)

    os.environ['GITHUB_RUN_ID'] = 'run_id'
    os.environ['GITHUB_REF'] = 'refs/pull/123'
    assert Coveralls.load_config_from_github() == (
        'github-actions', 'run_id', '123')
