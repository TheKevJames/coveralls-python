# coding: utf-8
import json
import logging
import os
import sys

import coverage
import pytest
import sh

from coveralls import Coveralls


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
NONUNICODE_DIR = os.path.join(BASE_DIR, 'nonunicode')


def test_non_unicode():
    os.chdir(NONUNICODE_DIR)
    sh.coverage('run', 'nonunicode.py')

    actual_json = json.dumps(Coveralls(repo_token='xxx').get_coverage())
    expected_json_part = (
        '"source": "# coding: iso-8859-15\\n\\n'
        'def hello():\\n'
        '    print(\'I like P\\u00f3lya distribution.\')')
    assert expected_json_part in actual_json


@pytest.mark.skipif(sys.version_info >= (3, 0), reason='python 3 not affected')
@pytest.mark.skipif(coverage.__version__.startswith('4.'),
                    reason='coverage 4 not affected')
def test_malformed_encoding_declaration(capfd):
    os.chdir(NONUNICODE_DIR)
    sh.coverage('run', 'malformed.py')

    logging.getLogger('coveralls').addHandler(logging.StreamHandler())
    assert Coveralls(repo_token='xxx').get_coverage() == []

    _, err = capfd.readouterr()
    assert 'Source file malformed.py can not be properly decoded' in err


@pytest.mark.skipif(sys.version_info < (3, 0), reason='python 2 fails')
@pytest.mark.skipif(coverage.__version__.startswith('3.'),
                    reason='coverage 3 fails')
def test_malformed_encoding_declaration_py3_or_coverage4():
    os.chdir(NONUNICODE_DIR)
    sh.coverage('run', 'malformed.py')

    result = Coveralls(repo_token='xxx').get_coverage()
    assert len(result) == 1

    assert result[0]['coverage'] == [None, None, 1, 0]
    assert result[0]['name'] == 'malformed.py'
    assert result[0]['source'].strip() == ('# -*- cоding: utf-8 -*-\n\n'
                                           'def hello():\n'
                                           '    return 1')
    assert 'branches' not in result[0]
