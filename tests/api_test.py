# coding: utf-8
import json

from coveralls import Coveralls


def test_output_to_file(tmpdir):
    """Check we can write coveralls report into the file."""
    test_log = tmpdir.join('test.log')
    Coveralls(repo_token='xxx').save_report(test_log.strpath)
    report = test_log.read()

    assert json.loads(report)['repo_token'] == 'xxx'
