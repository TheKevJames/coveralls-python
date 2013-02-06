# coding: utf-8
import json
import os
import tempfile
import coverage
import requests
import yaml
from .reporter import CoverallReporter


class Coveralls(object):
    config_filename = '.coveralls.yml'
    api_endpoint = 'https://coveralls.io/api/v1/jobs'
    default_client = 'coveralls-python'  # coveralls-ruby ?

    def __init__(self):
        """ Coveralls!

        * repo_token
          The secret token for your repository, found at the bottom of your repository's
           page on Coveralls.

        * service_name
          The CI service or other environment in which the test suite was run.
          This can be anything, but certain services have special features
          (travis-ci, travis-pro, or coveralls-ruby).

        * [service_job_id]
          A unique identifier of the job on the service specified by service_name.
        """
        self.config = {}
        file_config = yaml.load(open(self.config_filename))
        self.config['repo_token'] = file_config.get('repo_token', None)

        if not self.config['repo_token']:
            raise Exception('You have to provide repo_token in %s' % self.config_filename)

        if os.environ.get('TRAVIS'):
            self.config['service_name'] = file_config.get('service_name', None) or 'travis-ci'
            self.config['service_job_id'] = os.environ.get('TRAVIS_JOB_ID')
        else:
            self.config['service_name'] = file_config.get('service_name', None) or self.default_client

    def wear(self):
        """ run! """
        data = self.create_data()
        json_file, name = self.write_file(data)
        response = requests.post(self.api_endpoint, files={'json_file': json_file})
        os.remove(name)
        return response.json()

    def create_data(self):
        """ Generate object for api.
            Example json:
            {
                "service_job_id": "1234567890",
                "service_name": "travis-ci",
                "source_files": [
                    {
                        "name": "example.py",
                        "source": "def four\n  4\nend",
                        "coverage": [null, 1, null]
                    },
                    {
                        "name": "two.py",
                        "source": "def seven\n  eight\n  nine\nend",
                        "coverage": [null, 1, 0, null]
                    }
                ]
            }
        """
        data = {'source_files': self.get_coverage()}
        data.update(self.git_info())
        data.update(self.config)
        return data

    def write_file(self, data):
        fd, name = tempfile.mkstemp()
        json_file = open(name, 'w+')
        json.dump(data, json_file)
        json_file.close()
        return open(name, 'rb'), name

    def get_coverage(self):
        workman = coverage.coverage()
        workman.load()
        workman._harvest_data()
        reporter = CoverallReporter(workman, workman.config)
        return reporter.report()

    def git_info(self):
        # TODO: implement optional git info
        return {}
