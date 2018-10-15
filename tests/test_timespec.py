# Copyright (c) 2018 by Farsight Security, Inc.
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


import unittest


from axamd.client.__main__ import timespec_to_seconds


class TimespecTestCase(unittest.TestCase):

    def test_vanilla_1w1d1h1m1s(self):
        assert timespec_to_seconds('1w1d1h1m1s') == 694861

    def test_out_of_order_returns_none(self):
        assert timespec_to_seconds('1h1w') is None

    def test_vanilla_colon_delimited(self):
        assert timespec_to_seconds('01:01:01') == 3661
