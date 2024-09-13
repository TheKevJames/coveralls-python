import json
import os
import subprocess
import unittest
from unittest import mock

from coveralls import Coveralls


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
NONUNICODE_DIR = os.path.join(BASE_DIR, 'nonunicode')


class EncodingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_cwd = os.getcwd()

    @classmethod
    def tearDownClass(cls):
        os.chdir(cls.old_cwd)

    @staticmethod
    def test_non_unicode():
        os.chdir(NONUNICODE_DIR)
        subprocess.call(
            ['coverage', 'run', 'nonunicode.py'],
            cwd=NONUNICODE_DIR,
        )

        actual_json = json.dumps(Coveralls(repo_token='xxx').get_coverage())
        expected_json_part = (
            '"source": "# coding: iso-8859-15\\n\\n'
            'def hello():\\n'
            '    print(\'I like P\\u00f3lya distribution.\')'
        )
        assert expected_json_part in actual_json

    @staticmethod
    def test_malformed_encoding_declaration_py3_or_coverage4():
        os.chdir(NONUNICODE_DIR)
        subprocess.call(
            ['coverage', 'run', 'malformed.py'],
            cwd=NONUNICODE_DIR,
        )

        result = Coveralls(repo_token='xxx').get_coverage()
        assert len(result) == 1

        assert result[0]['coverage'] == [None, None, 1, 0]
        assert result[0]['name'] == 'malformed.py'
        assert result[0]['source'].strip() == (
            '# -*- cоding: utf-8 -*-\n\n'
            'def hello():\n'
            '    return 1'
        )
        assert 'branches' not in result[0]

    def test_debug_bad_encoding(self):
        data = {
            'source_files': [
                {
                    'name': 'bad_file.py',
                    'source': 'def foo():\n    return "foo"\n',
                    'coverage': [1, 1, 1],
                },
            ],
        }

        # Save the original json.dumps function
        original_json_dumps = json.dumps

        def mock_json_dumps(value):
            if value == 'def foo():\n    return "foo"\n':
                raise UnicodeDecodeError('utf8', b'', 0, 1, 'bad data')

            return original_json_dumps(value)

        with mock.patch(
            'coveralls.api.json.dumps',
            side_effect=mock_json_dumps,
        ):
            with mock.patch('coveralls.api.log') as mock_log:
                Coveralls.debug_bad_encoding(data)
                mock_log.error.assert_called()
