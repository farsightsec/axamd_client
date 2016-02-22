import os
import unittest

import jsonschema.validators
import pkg_resources
import yaml

class TestSchema():
    def load_schema(self, package, resource_name):
        f = pkg_resources.resource_stream(package, resource_name)
        self.config_schema = yaml.safe_load(f)
        f.close()

    def test_schema(self):
        validator = jsonschema.validators.validator_for(self.config_schema)
        validator.check_schema(self.config_schema)


class TestClientConfigSchema(TestSchema, unittest.TestCase):
    def setUp(self):
        self.load_schema('axamd.client', 'client-config-schema.yaml')

    def _test(self, instance):
        jsonschema.validate(instance, self.config_schema)

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


class TestStreamParamSchema(TestSchema, unittest.TestCase):
    def setUp(self):
        self.load_schema('axamd.client', 'stream-param-schema.yaml')


class TestChannelsOutputSchema(TestSchema, unittest.TestCase):
    def setUp(self):
        self.load_schema('axamd.client', 'channels-output-schema.yaml')


class TestAnomaliesOutputSchema(TestSchema, unittest.TestCase):
    def setUp(self):
        self.load_schema('axamd.client', 'anomalies-output-schema.yaml')

