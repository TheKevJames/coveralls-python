import json
import os
import pathlib
from unittest import mock

import coveralls


@mock.patch.dict(os.environ, {}, clear=True)
def test_output_to_file(tmp_path: pathlib.Path) -> None:
    """Check we can write coveralls report into the file."""
    test_log = tmp_path / 'test.log'
    coveralls.Coveralls(repo_token='xxx').save_report(str(test_log))
    report = test_log.read_text(encoding='utf-8')

    assert json.loads(report)['repo_token'] == 'xxx'
