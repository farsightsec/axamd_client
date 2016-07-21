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

import itertools

class AXAMDException(Exception):
    'Any exception raised by axamd.client.'

class Timeout(AXAMDException):
    'Raised when a connection times out.'

class ValidationError(AXAMDException):
    'Raised when query parameters fail to validate per the method\'s schema'

class ProblemDetails(AXAMDException):
    '''
    Details of a HTTP Problem report.

    This is an implementation of draft-ietf-appsawg-http-problem-03.
    All problem reports will contain the keys 'status', 'type' and 'title.'
    Some will contain 'details' and 'instance.'  All are defined per the
    referenced draft.  Some problem reports will contain additional keys
    with data to help diagnose an issue.  Please see README.md in the
    axamd.client source tree for further documentation.
    '''
    def __init__(self, problem):
        self.message = problem['title']
        if 'detail' in problem:
            self.message = '{}: "{}"'.format(self.message, problem['detail'])
        super(ProblemDetails, self).__init__(self.message)
        self._problem = problem

    def __getattr__(self, attr):
        if attr in self._problem:
            return self._problem['attr']
        raise AttributeError

    def keys(self):
        return self._problem.keys()

    def __getitem__(self, k):
        return self._problem[k]

    def __contains__(self, k):
        return k in self._problem

    def __str__(self):
        keys = ['status', 'type', 'title']
        optional_keys = ['detail', 'instance']
        extra_keys = sorted(set(self._problem.keys()).difference(keys).difference(optional_keys))
        lines = []
        for key in itertools.chain(keys, optional_keys, extra_keys):
            if key in self._problem:
                lines.append('{}: {}'.format(key, self._problem[key]))
        return '\n'.join(lines)

