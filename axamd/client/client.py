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

from .exceptions import ProblemDetails, ValidationError
from .six_mini import reraise
import requests
import json

try:
    import pkg_resources
    import yaml
    import jsonschema
    import sys

    _sra_stream_param_schema = yaml.safe_load(pkg_resources.resource_stream(__name__, 'sra-stream-param-schema.yaml'))
    _rad_stream_param_schema = yaml.safe_load(pkg_resources.resource_stream(__name__, 'rad-stream-param-schema.yaml'))

    def _gen_validate(schema):
        def _validate(instance):
            try:
                jsonschema.validate(instance, schema)
            except jsonschema.ValidationError:
                e,v,tb = sys.exc_info()
                reraise(ValidationError, v, tb)
        return _validate

    _sra_stream_param_validate = _gen_validate(_sra_stream_param_schema)
    _rad_stream_param_validate = _gen_validate(_rad_stream_param_schema)
except ImportError:
    # TODO debug log this
    def _sra_stream_param_validate(instance): pass
    def _rad_stream_param_validate(instance): pass

class Anomaly:
    def __init__(self, module, watches=None, options=None):
        self.module = module
        self.watches = watches
        self.options = options

    def to_dict(self):
        d = { 'module': self.module }
        if self.watches:
            d['watches'] = self.watches
        if self.options:
            d['options'] = self.options
        return d

    def __str__(self):
        return '{}{}: [{}]'.format(self.watches,
                self.options and ' '+self.options or '', # prefix with space
                ', '.join('[{}]'.format(w) for w in self.watches))
class _rq_ctx:
    def __enter__(self): pass
    def __exit__(self, e, v, tb):
        if isinstance(v, requests.HTTPError):
            try:
                reraise(ProblemDetails, ProblemDetails(v.response.json()), tb)
            except (KeyError, ValueError):
                pass

class Client:
    def __init__(self, server, apikey):
        self._server = server
        self._apikey = apikey

    def _stream(self, uri, validate=None, timeout=None, **stream_params):
        if validate:
            validate(stream_params)
        with _rq_ctx():
            r = requests.post(uri, data=json.dumps(stream_params),
                    headers={ 'X-API-Key': self._apikey },
                    timeout=timeout, stream=True)
            r.raise_for_status()
            return r.iter_lines()

    def _get(self, uri, timeout=None):
        with _rq_ctx():
            r = requests.get(uri, 
                    headers={ 'X-API-Key': self._apikey },
                    timeout=timeout)
            r.raise_for_status()
            return r.json()

    def sra(self, channels=[], watches=[], **params):
        uri='{}/v1/sra/stream'.format(self._server)
        return self._stream(uri,
                validate=_sra_stream_param_validate,
                channels=channels, watches=watches, **params)

    def rad(self, anomalies=[], **params):
        uri='{}/v1/rad/stream'.format(self._server)
        return self._stream(uri,
                validate=_rad_stream_param_validate,
                anomalies=[a.to_dict() for a in anomalies],
                **params)

    def list_channels(self, timeout=None):
        uri='{}/v1/sra/channels'.format(self._server)
        return self._get(uri, timeout=timeout)

    def list_anomalies(self, timeout=None):
        uri='{}/v1/rad/anomalies'.format(self._server)
        return self._get(uri, timeout=timeout)
