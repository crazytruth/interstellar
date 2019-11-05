#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read()

version = '0.1.0.dev0'

requirements = [
    'insanic>=0.8.3',
    'grpclib>=0.3.0',
    'grpcio-tools',
    'googleapis-common-protos',
    'protobuf'
]

setup_requirements = ['pytest-runner', ]

test_requirements = [
    'pytest',
    'grpc-test-monkey',
    "coverage",
    "pytest-cov",
    "pytest-sanic",
    "pytest-sugar",
    "pytest-xdist",
]

docs_requirements = ['sphinx', 'sphinx_rtd_theme']

cli_requirements = ['Click>=6.0']

release_requirements = ['zest.releaser[recommended]', 'flake8']

setup(
    author="Kwang Jin Kim",
    author_email='david@mymusictaste.com',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    description="A grpc plugin for interservice communications for insanic.",
    entry_points={
        'console_scripts': [
            'interstellar=interstellar.cli:cli',
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + '\n\n' + history,
    include_package_data=True,
    keywords='interstellar',
    name='interstellar',
    packages=find_packages(include=['interstellar']),
    setup_requires=setup_requirements,
    extras_require={
        "development": test_requirements + docs_requirements + cli_requirements + release_requirements,
        "cli": cli_requirements,
        "docs": docs_requirements
    },
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/MyMusicTaste/interstellar',
    version=version,
    zip_safe=False,
)
