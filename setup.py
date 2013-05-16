from setuptools.command.test import test as TestCommand
from setuptools import setup
import sys


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='coveralls',
    version='0.2.0',
    packages=['tests', 'coveralls'],
    url='http://github.com/coagulant/coveralls-python',
    license='MIT',
    author='Ilya Baryshev',
    author_email='baryhsev@gmail.com',
    description='Show coverage stats online via coveralls.io',
    scripts=['bin/coveralls'],
    install_requires=['PyYAML>=3.10', 'docopt>=0.6.1', 'coverage>=3.6', 'requests>=1.0.0', 'sh>=1.08'],
    tests_require=['mock', 'pytest'],
    cmdclass = {'test': PyTest},
    classifiers=[
        'Development Status :: 4 - Beta',
        'Topic :: Software Development :: Testing',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
    ],
)
