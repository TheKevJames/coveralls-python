import os

from setuptools import setup


VERSION_FILE = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                            'coveralls', 'version.py')

DESCRIPTION = open('README.rst').read()

VERSION = None
with open(VERSION_FILE, 'r') as f:
    VERSION = f.read().split()[2][1:-1]


setup(
    name='coveralls',
    version=VERSION,
    packages=['coveralls'],
    url='http://github.com/coveralls-clients/coveralls-python',
    project_urls={
        'Changelog': ('https://github.com/coveralls-clients/coveralls-python/'
                      'blob/master/CHANGELOG.md'),
        'Docs': 'https://coveralls-python.rtfd.io/',
    },
    license='MIT',
    author='coveralls-clients contributors',
    description='Show coverage stats online via coveralls.io',
    long_description=DESCRIPTION,
    entry_points={
        'console_scripts': [
            'coveralls = coveralls.cli:main',
        ],
    },
    install_requires=['docopt>=0.6.1', 'coverage>=3.6', 'requests>=1.0.0'],
    setup_requires=['pytest-runner'],
    tests_require=['mock', 'pytest', 'sh>=1.08'],
    extras_require={
        'yaml': ['PyYAML>=3.10'],
        ':python_version < "3"': ['urllib3[secure]'],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Topic :: Software Development :: Testing',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
)
