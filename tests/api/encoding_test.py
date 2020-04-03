import json
import os
import subprocess

import coverage
import pytest

from coveralls import Coveralls


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
NONUNICODE_DIR = os.path.join(BASE_DIR, 'nonunicode')


def test_non_unicode():
    os.chdir(NONUNICODE_DIR)
    subprocess.call(['coverage', 'run', 'nonunicode.py'], cwd=NONUNICODE_DIR)

    actual_json = json.dumps(Coveralls(repo_token='xxx').get_coverage())
    expected_json_part = (
        '"source": "# coding: iso-8859-15\\n\\n'
        'def hello():\\n'
        '    print(\'I like P\\u00f3lya distribution.\')')
    assert expected_json_part in actual_json


@pytest.mark.skipif(coverage.__version__.startswith('3.'),
                    reason='coverage 3 fails')
def test_malformed_encoding_declaration_py3_or_coverage4():
    os.chdir(NONUNICODE_DIR)
    subprocess.call(['coverage', 'run', 'malformed.py'], cwd=NONUNICODE_DIR)

    result = Coveralls(repo_token='xxx').get_coverage()
    assert len(result) == 1

    assert result[0]['coverage'] == [None, None, 1, 0]
    assert result[0]['name'] == 'malformed.py'
    assert result[0]['source'].strip() == ('# -*- cоding: utf-8 -*-\n\n'
                                           'def hello():\n'
                                           '    return 1')
    assert 'branches' not in result[0]
