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

import unittest

import jsonschema.validators
import pkg_resources
import yaml

class TestSchema():
    @classmethod
    def load_schema(cls, package, resource_name):
        f = pkg_resources.resource_stream(package, resource_name)
        cls.schema = yaml.safe_load(f)
        f.close()

    def test_schema(self):
        validator = jsonschema.validators.validator_for(self.__class__.schema)
        validator.check_schema(self.__class__.schema)


class TestClientConfigSchema(TestSchema, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.load_schema('axamd.client', 'client-config-schema.yaml')

    def _test(self, instance):
        jsonschema.validate(instance, self.__class__.schema)

    def _test_invalid(self, instance):
        with self.assertRaises(jsonschema.ValidationError):
            self._test(instance)

    def test_full_config(self):
        self._test({
            'server': 'https://axamd.sra-network.net',
            'apikey': '<elided>',
            'timeout': 1,
            'sample-rate': 1,
            'rate-limit': 1,
            'report-interval': 1,
            'retries': 1,
            'retry-backoff': 1
            })

    def test_extra_keys(self):
        self._test({'extra': True})

    def _test_string(self, key):
        self._test_invalid({key: None})
        self._test_invalid({key: 1})
        self._test_invalid({key: True})
        self._test_invalid({key: ''})
        self._test_invalid({key: {}})
        self._test_invalid({key: []})

    def test_invalid_server(self):
        self._test_string('server')

    def test_invalid_apikey(self):
        self._test_string('apikey')

    def _test_number(self, key, minimum=None, maximum=None):
        if minimum is not None:
            self._test({key: minimum})
            self._test_invalid({key: minimum-1})
        if maximum is not None:
            self._test({key: maximum})
            self._test_invalid({key: maximum+1})

        self._test_invalid({key: None})
        self._test_invalid({key: True})
        self._test_invalid({key: ''})
        self._test_invalid({key: 'a longer string'})
        self._test_invalid({key: {}})
        self._test_invalid({key: []})

    def _test_integer(self, key, minimum=None, maximum=None):
        self._test_number(key, minimum=minimum, maximum=maximum)
        if minimum is not None:
            self._test_invalid({key: float(minimum)})
            self._test_invalid({key: minimum-1.0})
        if maximum is not None:
            self._test_invalid({key: float(maximum)})
            self._test_invalid({key: maximum+1.0})

    def test_timeout(self):
        self._test_number('timeout', minimum=1)

    def test_sample_rate(self):
        self._test_number('sample-rate', minimum=0.1, maximum=100.0)

    def test_rate_limit(self):
        self._test_integer('rate-limit', minimum=1)

    def test_report_interval(self):
        self._test_integer('report-interval', minimum=1)


class TestSRAStreamParamSchema(TestSchema, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.load_schema('axamd.client', 'sra-stream-param-schema.yaml')


class TestRADStreamParamSchema(TestSchema, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.load_schema('axamd.client', 'rad-stream-param-schema.yaml')


class TestChannelsOutputSchema(TestSchema, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.load_schema('axamd.client', 'channels-output-schema.yaml')


class TestAnomaliesOutputSchema(TestSchema, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.load_schema('axamd.client', 'anomalies-output-schema.yaml')


class TestAXAJSONSchema(TestSchema, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.load_schema('axamd.client', 'axa-json-schema.yaml')

axa_json_strings = '''\
{"tag":4,"op":"HELLO","id":1,"pvers_min":2,"pvers_max":3,"str":"hello"}
{"tag":"*","op":"JOIN","id":0}
{"tag":1,"op":"OK","orig_op":"WATCH HIT","str":"success"}
{"tag":1,"op":"ERROR","orig_op":"OK","str":"failure"}
{"tag":1,"op":"MISSED","missed":2,"dropped":3,"rlimit":4,"filtered":5,"last_report":6}
{"tag":1,"op":"RAD MISSED","sra_missed":2,"sra_dropped":3,"sra_rlimit":4,"sra_filtered":5,"dropped":6,"rlimit":7,"filtered":8,"last_report":9}
{"tag":1,"op":"WATCH HIT","channel":"ch123","field_idx":1,"val_idx":2,"vname":"base","mname":"pkt","time":"1970-01-01 00:00:01.000000002","nmsg":{"time":"1970-01-01 00:00:01.000000002","vname":"base","mname":"pkt","message":{"len_frame":32,"payload":"RQAAIBI0QAD/EVmFAQIDBAUGBwgAewHIAAxP4t6tvu8="}}}
{"tag":1,"op":"WATCH HIT","channel":"ch123","time":"1970-01-01 00:00:01.000002","af":"IPv4","src":"1.2.3.4","dst":"5.6.7.8","ttl":255,"proto":"UDP","src_port":123,"dst_port":456,"payload":"3q2+7w=="}
{"tag":1,"op":"WATCH HIT","channel":"ch123","time":"1970-01-01 00:00:01.000002","af":"IPv4","src":"1.2.3.4","dst":"5.6.7.8","ttl":255,"proto":"TCP","src_port":123,"dst_port":456,"flags":["SYN","ACK"],"payload":"3q2+7w=="}
{"tag":1,"op":"WATCH HIT","channel":"ch123","time":"1970-01-01 00:00:01.000002","af":"IPv6","src":"1:2:3:4:5:6:7:8","dst":"9:0:a:b:c:d:e:f","ttl":255,"proto":"UDP","src_port":123,"dst_port":456,"payload":"3q2+7w=="}
{"tag":1,"op":"WATCH","watch_type":"ipv4","watch":"IP=12.34.56.0/24"}
{"tag":1,"op":"WATCH","watch_type":"ipv4","watch":"IP=0.0.0.0/24"}
{"tag":1,"op":"WATCH","watch_type":"ipv4","watch":"IP=12.34.56.78/24"}
{"tag":1,"op":"WATCH","watch_type":"ipv6","watch":"IP=1:2:3:4:5:6::/48"}
{"tag":1,"op":"WATCH","watch_type":"dns","watch":"dns=fsi.io"}
{"tag":1,"op":"WATCH","watch_type":"dns","watch":"dns=*.fsi.io"}
{"tag":1,"op":"WATCH","watch_type":"dns","watch":"dns=*."}
{"tag":1,"op":"WATCH","watch_type":"dns","watch":"dns=fsi.io(shared)"}
{"tag":1,"op":"WATCH","watch_type":"channel","watch":"ch=123"}
{"tag":1,"op":"WATCH","watch_type":"errors","watch":"ERRORS"}
{"tag":1,"op":"ANOMALY","an":"test_anom","parms":"param1 param2"}
{"tag":1,"op":"CHANNEL ON/OFF","channel":"ch123","on":true}
{"tag":1,"op":"CHANNEL ON/OFF","channel":"ch123","on":false}
{"tag":1,"op":"CHANNEL ON/OFF","channel":"all","on":true}
{"tag":1,"op":"WATCH LIST","cur_tag":1,"watch_type":"ipv4","watch":"IP=12.34.56.0/24"}
{"tag":1,"op":"ANOMALY HIT","an":"test_anom","channel":"ch123","time":"1970-01-01 00:00:01.000002","af":"IPv4","src":"1.2.3.4","dst":"5.6.7.8","ttl":255,"proto":"UDP","src_port":123,"dst_port":456,"payload":"3q2+7w=="}
{"tag":1,"op":"ANOMALY LIST","cur_tag":1,"an":"test_anom","parms":"param1 param2"}
{"tag":1,"op":"CHANNEL LIST","channel":"ch123","on":true,"spec":"test channel"}
{"tag":1,"op":"USER","name":"test user"}
{"tag":1,"op":"OPTION","type":"TRACE","trace":3}
{"tag":1,"op":"OPTION","type":"TRACE","trace":"REQUEST TRACE VALUE"}
{"tag":1,"op":"OPTION","type":"RATE LIMIT","max_pkts_per_sec":123,"cur_pkts_per_sec":456,"report_secs":60}
{"tag":1,"op":"OPTION","type":"RATE LIMIT","max_pkts_per_sec":1000000000,"cur_pkts_per_sec":123,"report_secs":60}
{"tag":1,"op":"OPTION","type":"RATE LIMIT","max_pkts_per_sec":"off","cur_pkts_per_sec":123,"report_secs":60}
{"tag":1,"op":"OPTION","type":"RATE LIMIT","max_pkts_per_sec":null,"cur_pkts_per_sec":123,"report_secs":null}
{"tag":1,"op":"OPTION","type":"SAMPLE","sample":0.000123}
{"tag":1,"op":"OPTION","type":"SNDBUF","bufsize":123}'''.split('\n')

def gen_test_yaml(s):
    def test_yaml_string(self):
        jsonschema.validate(yaml.safe_load(s), self.__class__.schema)
    return test_yaml_string
for s in axa_json_strings:
    setattr(TestAXAJSONSchema, 'test_validate({})'.format(s), gen_test_yaml(s))
