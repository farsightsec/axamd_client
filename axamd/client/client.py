from .exceptions import ProblemDetails, ValidationError
from .six_mini import reraise
import requests
import json

try:
    import pkg_resources
    import yaml
    import jsonschema
    import sys

    _stream_param_schema = yaml.safe_load(pkg_resources.resource_stream(__name__, 'stream-param-schema.yaml'))

    def _stream_params_validate(stream_params):
        try:
            jsonschema.validate(stream_params, _stream_param_schema)
        except jsonschema.ValidationError:
            e,v,tb = sys.exc_info()
            reraise(ValidationError, v, tb)
except ImportError:
    # TODO debug log this
    def _stream_params_validate(stream_params):
        pass

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

    def _stream(self, uri, timeout=None, **stream_params):
        _stream_params_validate(stream_params)
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
        return self._stream(uri, channels=channels, watches=watches, **params)

    def rad(self, anomalies=[], **params):
        uri='{}/v1/rad/stream'.format(self._server)
        return self._stream(uri, anomalies=[a.to_dict() for a in anomalies],
                **params)

    def list_channels(self, timeout=None):
        uri='{}/v1/sra/channels'.format(self._server)
        return self._get(uri, timeout=timeout)

    def list_anomalies(self, timeout=None):
        uri='{}/v1/rad/anomalies'.format(self._server)
        return self._get(uri, timeout=timeout)
