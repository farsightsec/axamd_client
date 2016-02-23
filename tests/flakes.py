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
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
import unittest

import axamd.client
import pyflakes.api
import pyflakes.reporter
import tests

class TestFlakes(unittest.TestCase):
    pass

def gen_tcase(fn):
    def _tcase(self):
        errors = StringIO()
        reporter = pyflakes.reporter.Reporter(errors, errors)
        f = open(fn)
        pyflakes.api.check(f.read(), fn, reporter=reporter)
        f.close()
        if errors.tell():
            self.fail(errors.getvalue())
    return _tcase

for module in (axamd.client, tests):
    base_dir = os.path.dirname(module.__file__)
    for fn in pyflakes.api.iterSourceCode([base_dir]):
        tname = fn[len(base_dir)+1:-3]
        setattr(TestFlakes,
                'test_flakes({}.{})'.format(module.__name__, tname),
                gen_tcase(fn))
