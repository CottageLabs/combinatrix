import sys
from setuptools import setup, find_packages

setup(
    name = 'combinatrix',
    version = '1.0.0',
    packages = find_packages(),
    install_requires = [
        "parameterized==0.6.1"
    ],
    url = 'http://cottagelabs.com/',
    author = 'Cottage Labs',
    author_email = 'us@cottagelabs.com',
    description = 'Produce constrained combinations of parameters',
    classifiers = [
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
