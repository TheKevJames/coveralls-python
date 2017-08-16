# coding: utf-8
from __future__ import unicode_literals

import json
import logging
import os
import sys

import coverage
import sh
import pytest

from coveralls import Coveralls


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
NONUNICODE = os.path.join(ROOT_DIR, 'nonunicode')


def test_non_unicode():
    os.chdir(NONUNICODE)
    sh.coverage('run', 'nonunicode.py')

    coverage_obj = Coveralls(repo_token='xxx').get_coverage()
    result = json.dumps(coverage_obj)
    assert (
        '"source": "# coding: iso-8859-15\\n\\n'
        'def hello():\\n'
        '    print (\'I like P\\u00f3lya distribution.\')\\n') in result


@pytest.mark.skipif(sys.version_info >= (3, 0), reason='python 3 not affected')
@pytest.mark.skipif(coverage.__version__.startswith('4.'),
                    reason='coverage 4 not affected')
def test_malformed_encoding_declaration(capfd):
    os.chdir(NONUNICODE)
    sh.coverage('run', 'malformed.py')

    logging.getLogger('coveralls').addHandler(logging.StreamHandler())
    coverage_obj = Coveralls(repo_token='xxx').get_coverage()
    assert coverage_obj == []

    _, err = capfd.readouterr()
    assert 'Source file malformed.py can not be properly decoded' in err


@pytest.mark.skipif(
    sys.version_info < (3, 0) or coverage.__version__.startswith('3.'),
    reason='python 2 or coverage 3 fail')
def test_malformed_encoding_declaration_py3_or_coverage4():
    os.chdir(NONUNICODE)
    sh.coverage('run', 'malformed.py')

    logging.getLogger('coveralls').addHandler(logging.StreamHandler())
    result_obj = Coveralls(repo_token='xxx').get_coverage()
    assert len(result_obj) == 1

    assert result_obj[0]['source'].strip() == ('# -*- cоding: utf-8 -*-\n\n'
                                               'def hello():\n'
                                               '    return 1')
    assert result_obj[0]['name'] == 'malformed.py'
    assert result_obj[0]['coverage'] == [None, None, 1, 0]
    assert result_obj[0].get('branches') is None
