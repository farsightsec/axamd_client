#!/usr/bin/env python

# Copyright (c) 2016 by Farsight Security, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from setuptools import setup

setup(
    name = 'axamd.client',
    version = '1.0.0',
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
    ],
    test_suite='tests',
    tests_require = [
        'pyflakes',
    ],
)
