# coding: utf-8
from __future__ import unicode_literals

import json
import logging
import os
import sys

import coverage
import pytest
import sh

from coveralls import Coveralls


def test_non_unicode():
    os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nonunicode'))
    sh.coverage('run', 'nonunicode.py')
    expected_json_part = '"source": "# coding: iso-8859-15\\n\\ndef hello():\\n    print(\'I like P\\u00f3lya distribution.\')'
    assert expected_json_part in json.dumps(Coveralls(repo_token='xxx').get_coverage())


@pytest.mark.skipif(sys.version_info >= (3, 0), reason='python 3 not affected')
@pytest.mark.skipif(coverage.__version__.startswith('4.'), reason='coverage 4 not affected')
def test_malformed_encoding_declaration(capfd):
    os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nonunicode'))
    sh.coverage('run', 'malformed.py')
    logging.getLogger('coveralls').addHandler(logging.StreamHandler())
    result_object = Coveralls(repo_token='xxx').get_coverage()
    assert result_object == []
    _, err = capfd.readouterr()
    assert 'Source file malformed.py can not be properly decoded' in err


@pytest.mark.skipif(sys.version_info < (3, 0) or coverage.__version__.startswith('3.'),
                    reason='python 2 or coverage 3 fail')
def test_malformed_encoding_declaration_py3_or_coverage4():
    os.chdir(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nonunicode'))
    sh.coverage('run', 'malformed.py')
    logging.getLogger('coveralls').addHandler(logging.StreamHandler())
    result_object = Coveralls(repo_token='xxx').get_coverage()
    assert len(result_object) == 1

    assert result_object[0]['coverage'] == [None, None, 1, 0]
    assert result_object[0]['name'] == 'malformed.py'
    assert result_object[0]['source'].strip() == ('# -*- cоding: utf-8 -*-\n\n'
                                                  'def hello():\n'
                                                  '    return 1')
    assert 'branches' not in result_object[0]


def test_output_to_file(tmpdir):
    """Check we can write coveralls report into the file."""

    test_log = tmpdir.join('test.log')
    Coveralls(repo_token='xxx').save_report(test_log.strpath)
    report = test_log.read()
    assert json.loads(report)['repo_token'] == 'xxx'
