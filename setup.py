from setuptools import setup

setup(
    name='coveralls-python',
    version='0.1',
    packages=['tests', 'coveralls'],
    url='http://github.com/coagulant/coveralls-python',
    license='MIT',
    author='Ilya Baryshev',
    author_email='baryhsev@gmail.com',
    description='Show coverage stats online via coveralls.io',
    scripts=['bin/coveralls'],
    install_requires=['PyYAML', 'docopt', 'coverage', 'requests', 'sh'],
    tests_require=['nose', 'sure', 'mock'],
    test_suite="nose.collector",
    classifiers=[
        'Development Status :: 3 - Alpha',
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
