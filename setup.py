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
    requires=['docopt', 'coverage', 'requests'],
)
