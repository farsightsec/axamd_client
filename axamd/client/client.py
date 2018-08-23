# Copyright (c) 2016, 2018 by Farsight Security, Inc.
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

'''
Client for the Farsight Advanced Exchange Access (AXA) RESTful Interface

The Farsight AXA RESTful Interface adds a streaming HTTP interface on
top of the [AXA toolkit](https://www.github.com/farsightsec/axa) to
enable developers of web-based applications to interface with Farsight's
SRA (SIE Remote Access) and RAD (Realtime Anomaly Detector) servers.

Example usage:

```python
from axamd.client import Client
import json
c = Client('https://axamd.sie-remote.net', apikey)
for line in c.sra(channels=[212], watches=['ch=212']):
    data = json.loads(line)
```
'''

import json
import platform

from . import __version__
from .exceptions import ProblemDetails, ValidationError, Timeout
from .six_mini import reraise

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

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


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    session = session or requests.Session()
    retry = Retry(
        method_whitelist=frozenset(['GET', 'POST']),
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


class Anomaly:
    '''
    The Anomaly module wraps the parameters and watches used to instantiate
    a RAD anomaly module.
    '''
    def __init__(self, module, watches=None, options=None):
        '''
        Args:
            module (string): RAD anomaly module name
            watches (list[string]): A list of watches for this anomaly module
            options (string): Parameter string for the anomaly module
        '''
        self.module = module
        self.watches = watches
        self.options = options

    def to_dict(self):
        '''
        Returns a dict that can be included in a parameter document.
        '''
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
        elif isinstance(v, requests.Timeout):
            reraise(Timeout, Timeout(v), tb)

class Client:
    user_agent = 'axamd.client/v{} {}/{} {}'.format(__version__,
            platform.python_implementation(), platform.python_version(),
            platform.platform())
    __doc__ = __doc__
    def __init__(self, server, apikey, retries=3, retry_backoff=0.3, proxy=None):
        '''
        Args:
            server (string): Server URI
            apikey (string): API key
        '''
        self._server = server
        self._apikey = apikey
        self._retries = retries
        self._backoff = retry_backoff
        self._proxies = {}
        if proxy:
            self._proxies['http'] = proxy
            self._proxies['https'] = proxy

    def _stream(self, uri, validate=None, timeout=None, **stream_params):
        if validate:
            validate(stream_params)
        with _rq_ctx():
            r = requests_retry_session(retries=self._retries, backoff_factor=self._backoff)\
                .post(uri, data=json.dumps(stream_params),
                    headers={
                        'X-API-Key': self._apikey,
                        'User-Agent': Client.user_agent,
                        },
                    proxies = self._proxies,
                    timeout=timeout, stream=True)
            r.raise_for_status()
            for line in r.iter_lines():
                yield line.lstrip(b'\x1e').decode('utf-8')

    def _get(self, uri, timeout=None):
        with _rq_ctx():
            r = requests_retry_session(retries=self._retries, backoff_factor=self._backoff).get(uri,
                    headers={
                        'X-API-Key': self._apikey,
                        'User-Agent': Client.user_agent,
                        },
                    proxies = self._proxies,
                    timeout=timeout)
            r.raise_for_status()
            return r.json()

    def sra(self, channels=[], watches=[], **params):
        '''
        Requests streaming data from the SRA server.  Tags for watches are
        automatically assigned based on 1 + offset.  Output can be in either
        axa format (default) or nmsg format, the latter of which can be
        directly loaded with nmsg.message.from_json.

        Args:
            channels (list[int]): Channel numbers to enable
            watches (list[string]): Watch strings
            sample_rate (float (0..1]): Sampling rate for the SRA server.
            rate_limit (int): Maximum watch hits per second.
            report_interval (int): Seconds between statistics messages.
            output_format (str): One of 'axa+json', or 'nmsg+json'.
            timeout (float): Socket timeout.
        Returns:
            iterator returning strings formatted per output_format
        Raises:
            ProblemDetails
            ValidationError
        '''
        uri='{}/v1/sra/stream'.format(self._server)
        return self._stream(uri,
                validate=_sra_stream_param_validate,
                channels=channels, watches=watches, **params)

    def rad(self, anomalies=[], **params):
        '''
        Requests streaming data from the RAD server.  Tags for watches are
        automatically assigned based on 1 + offset.  Output can be in either
        axa format (default) or nmsg format, the latter of which can be
        directly loaded with nmsg.message.from_json.

        Args:
            anomalies (list[Anomaly]): Anomaly objects
            sample_rate (float (0..1]): Sampling rate for the SRA server.
            rate_limit (int): Maximum watch hits per second.
            report_interval (int): Seconds between statistics messages.
            output_format (str): One of 'axa+json', or 'nmsg+json'.
            timeout (float): Socket timeout.
        Returns:
            iterator returning strings formatted per output_format
        Raises:
            ProblemDetails
            ValidationError
        '''
        uri='{}/v1/rad/stream'.format(self._server)
        return self._stream(uri,
                validate=_rad_stream_param_validate,
                anomalies=[a.to_dict() for a in anomalies],
                **params)

    def list_channels(self, timeout=None):
        '''
        Requests the list of available channels from the SRA server.
        Returns a dictionary mapping channel names (ch#) to descriptions.

        Args:
            timeout (float): Socket timeout.
        Raises:
            ProblemDetails
        '''
        uri='{}/v1/sra/channels'.format(self._server)
        return self._get(uri, timeout=timeout)

    def list_anomalies(self, timeout=None):
        '''
        Requests the list of available anomaly modules from the RAD server.
        Returns a dictionary mapping anomaly module names to descriptions.

        Args:
            timeout (float): Socket timeout.
        Raises:
            ProblemDetails
        '''
        uri='{}/v1/rad/anomalies'.format(self._server)
        return self._get(uri, timeout=timeout)
