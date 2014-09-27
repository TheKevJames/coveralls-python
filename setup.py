import sys
from setuptools.command.test import test as TestCommand
from setuptools import setup


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
    version='0.4.3',
    packages=['coveralls'],
    url='http://github.com/coagulant/coveralls-python',
    license='MIT',
    author='Ilya Baryshev',
    author_email='baryshev@gmail.com',
    description='Show coverage stats online via coveralls.io',
    long_description=open('README.rst').read() + '\n\n' + open('CHANGELOG.rst').read(),
    entry_points={
        'console_scripts': [
            'coveralls = coveralls.cli:main',
        ],
    },
    install_requires=['PyYAML>=3.10', 'docopt>=0.6.1', 'coverage>=3.6,<4.0', 'requests>=1.0.0'],
    tests_require=['mock', 'pytest', 'sh>=1.08'],
    cmdclass={'test': PyTest},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Topic :: Software Development :: Testing',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
