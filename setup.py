from setuptools import setup


DESCRIPTION = open('README.rst').read() + '\n\n' + open('CHANGELOG.rst').read()


setup(
    name='coveralls',
    version='1.1',
    packages=['coveralls'],
    url='http://github.com/coagulant/coveralls-python',
    license='MIT',
    author='Ilya Baryshev',
    author_email='baryshev@gmail.com',
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
        'yaml': ['PyYAML>=3.10']
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Topic :: Software Development :: Testing',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
