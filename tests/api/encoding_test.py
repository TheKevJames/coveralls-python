import json
import os
import subprocess
import unittest.mock
from typing import Any

import pytest

from coveralls import Coveralls


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
NONUNICODE_DIR = os.path.join(BASE_DIR, 'nonunicode')


class TestEncoding:
    @staticmethod
    def test_non_unicode(monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.chdir(NONUNICODE_DIR)
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
    def test_malformed_encoding_declaration_py3_or_coverage4(
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.chdir(NONUNICODE_DIR)
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

    @staticmethod
    def test_debug_bad_encoding() -> None:
        data = {
            'source_files': [
                {
                    'name': 'bad_file.py',
                    'source': 'def foo():\n    return "foo"\n',
                    'coverage': [1, 1, 1],
                },
            ],
        }

        original_json_dumps = json.dumps

        def mock_json_dumps(value: Any) -> str:
            if value == 'def foo():\n    return "foo"\n':
                raise UnicodeDecodeError('utf8', b'', 0, 1, 'bad data')

            return original_json_dumps(value)

        with unittest.mock.patch(
                'coveralls.api.json.dumps',
                side_effect=mock_json_dumps,
        ), unittest.mock.patch(
                'coveralls.api.log',
        ) as mock_log:
            Coveralls.debug_bad_encoding(data)
            mock_log.error.assert_called()
            assert mock_log.error.call_args_list[0][0][1] == 'bad_file.py'
