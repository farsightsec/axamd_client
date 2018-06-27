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

import os

from setuptools import setup

base_dir = os.path.dirname(__file__)
about = {}
with open(os.path.join(base_dir, 'axamd', 'client', '__about__.py')) as f:
    exec(f.read(), about)

setup(
    name = about['__title__'],
    description = about['__description__'],
    version = about['__version__'],
    author = about['__author__'],
    author_email = about['__author_email__'],
    url = about['__uri__'],
    classifiers = about['__classifiers__'],
    license = about['__license__'],

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
