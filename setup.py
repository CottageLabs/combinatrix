from setuptools import setup, find_packages

setup(
    name='combinatrix',
    version='2.0.0',
    packages=find_packages(),
    install_requires=[
        "parameterized~=0.9.0"
    ],
    url='http://cottagelabs.com/',
    author='Cottage Labs',
    author_email='us@cottagelabs.com',
    description='Produce constrained combinations of parameters',
    classifiers=[
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points={
        'console_scripts': [
            'combinatrix=combinatrix.cli:main',
        ],
    }
)
