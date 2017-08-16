# coding: utf-8
from __future__ import unicode_literals

import os
import unittest

import mock
import pytest
try:
    import yaml
except ImportError:
    yaml = None

from coveralls import Coveralls
from coveralls.api import log


@mock.patch.object(Coveralls, 'config_filename', '.coveralls.mock')
class Configuration(unittest.TestCase):
    def setUp(self):
        with open('.coveralls.mock', 'w+') as fp:
            fp.write('repo_token: xxx\n')
            fp.write('service_name: jenkins\n')

    def tearDown(self):
        os.remove('.coveralls.mock')

    @pytest.mark.skipif(yaml is None, reason='requires PyYAML')
    @mock.patch.dict(os.environ, {}, clear=True)
    def test_local_with_config(self):
        cover = Coveralls()
        assert cover.config['service_name'] == 'jenkins'
        assert cover.config['repo_token'] == 'xxx'
        assert 'service_job_id' not in cover.config

    @pytest.mark.skipif(yaml is not None, reason='requires no PyYAML')
    @mock.patch.object(log, 'warning')
    def test_local_with_config_without_yaml_module(self, mock_logger):
        """test local with config in yaml, but without yaml-installed"""
        Coveralls()
        mock_logger.assert_called_once_with(
            'PyYAML is not installed, ignoring .coveralls.mock')
