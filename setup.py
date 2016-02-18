#!/usr/bin/env python

# Copyright (c) 2016 Farsight Security, Inc.
# All Rights Reserved
#
# THIS IS UNPUBLISHED PROPRIETARY SOURCE CODE OF FARSIGHT SECURITY, INC.
# The copyright notice above does not evidence any
# actual or intended publication of such source code.

from setuptools import setup

setup(
    name = 'axamd.client',
    version = '0.0.0',
    author = 'Farsight Security, Inc.',
    author_email = 'software@farsightsecurity.com',
    url = 'https://github.com/farsightsec/axamd_client',
    classifiers = [
        'License :: OSI Approved :: Apache Software License',
    ],
    packages = ['axamd','axamd.client'],
    namespace_packages = ['axamd'],
    package_data = {
        '': ['*.yaml'],
    },
    entry_points = {
        'console_scripts': [
            'axamd_client = axamd.client.__main__:main',
        ]
    },
    install_requires = [
        'jsonschema',
        'option_merge',
        'pyyaml',
        'requests',
        'six',
    ],
    test_suite='tests',
)
