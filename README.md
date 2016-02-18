# Farsight Advanced Exchange Access RESTful Interface

The purpose of Farsight's Advanced Exchange Access (AXA) toolkit is to bring
the capabilities of the Farsight Security Information Exchange (SIE) right to
the subscriber's network edge rather than requiring a direct connection to the
SIE.

The Farsight AXA RESTful Interface adds a streaming HTTP interface on top of the
AXA toolkit to enable developers of web-based applications to interface 
with Farsight's SRA (SIE Remote Access) and RAD (Realtime Anomaly Detector)
servers.

SRA and RAD services are delivered via Farsight's RESTful AXA protocol which
allows session initiators to control a number of parameters including:

 * select SIE channels (SRA)
 * specify DNS and IP address watch patterns (SRA and RAD)
 * control packet rate limits and sampling rate
 * set anomaly watches and specify anomaly modules (RAD)

Access is controlled via an API key that is passed as the `X-API-Key` HTTP
header.

## SIE Remote Access (SRA)

## Realtime Anomaly Detector (RAD)

## AXA Watch Format

| Watch Type | Syntax | Notes |
| --- | --- | --- |
| Channel | `ch=<#>` | SIE channel number. Not supported in RAD mode. |
| IP Address | `ip=<ipv4 or ipv6 literal>` | In CIDR notation |
| Domain Name | `dns=<domain>` | Supports wildcards `*.` or `*.example.com` |

## Python Reference Implementation

* Python setup.py install.  A full-featured client is installed as `axamd_client`.  You may configure the client using /etc/axamd-client.conf, ~/.axamd-client.conf, or any file you specify on the command line.  You may forego this and use only command line options if you prefer.  Configuration files are YAML or JSON objects.  Allowable keys are:

| Option | Type | Description |
| --- | --- | --- |
| `server` | string | URI to AXAMD server |
| `apikey` | string | Key for authentication |
| `timeout` | number | Socket timeout in seconds |
| `sample-rate` | number | Channel sampling rate (percent) |
| `rate-limit` | integer | Maximum packets per second |
| `report-interval` | integer | Seconds between server statistics messages |

See [client-config-schema.yaml](axamd/client/client-config-schema.yaml) for more details.

The client can be called from the command line as follows:

```
usage: axamd_client [-h] [--config CONFIG] [--server SERVER] [--apikey APIKEY]
                 [--timeout TIMEOUT] [--rate-limit PPS]
                 [--report-interval SECONDS] [--sample-rate PERCENTAGE]
                 [--list-channels] [--list-anomalies]
                 [--channels [CHANNEL [CHANNEL ...]]]
                 [--watches WATCH [WATCH ...]]
                 [--anomaly [MODULE [OPTIONS ...]]] [--debug]

Client for the AXA RESTful Interface

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to config file
  --server SERVER, -s SERVER
                        AXAMD server
  --apikey APIKEY, -k APIKEY
                        API key
  --timeout TIMEOUT, -t TIMEOUT
                        Timeout for connections
  --rate-limit PPS, -l PPS
                        AXA rate limit
  --report-interval SECONDS, -i SECONDS
                        AXA report interval
  --sample-rate PERCENTAGE, -r PERCENTAGE
                        AXA sample rate (percentage)
  --list-channels       List available channels
  --list-anomalies      List available anomalies
  --channels [CHANNEL [CHANNEL ...]], -C [CHANNEL [CHANNEL ...]]
                        SRA mode: Channels to listen on
  --watches WATCH [WATCH ...], -W WATCH [WATCH ...]
                        SRA/RAD mode: Watch list
  --anomaly [MODULE [OPTIONS ...]], -A [MODULE [OPTIONS ...]]
                        RAD mode: Anomaly module and options
  --debug               Debug mode

```

The client may also be used programmatically.  It is compatible with both Python 2 and Python 3.  The client raises axamd.ProblemDetails excepetions from server errors corresponding to the internet draft `draft-ietf-appsawg-http-problem-03`.  See `pydoc axamd.client.Client` for full details.  Example usage:

```python
from axamd.client import Client, Anomaly
import json

apikey = '00000000-0000-0000-0000-00000000'
c = Client('https://axamd.sie-network.net', apikey)

for line in c.sra(channels=[212], watches=['ch=212']):
    data = json.loads(line)

# or

import nmsg

for line in c.rad(anomalies=[Anomaly('dns_match', ['dns=*.'], 'match=com')],
        output_format='nmsg+json'):
    msg = nmsg.message.from_json(line)
```

While the distribution has several python dependencies, `axamd.client.Client` only depends on the Python requests module.  You can enable schema validation by importing `axamd.client.schema.stream_params_validate` and passing that as the `stream_params_validate` parameter to `Client`.  This adds depdencies on pyyaml and jsonschema.

## Protocol

### Channel List

* **URL**

  `/v1/sra/channels`

* **METHOD**

  `GET`

* **Success Response:**

  **Code:** 200  
  **Content:** `{ "ch14": "Darknet data" }`

```yaml
id: http://farsightsecurity.com/axamd-channels-output-schema#
$schema: http://json-schema.org/draft-04/schema#
title: axamd channels output schema
description: Schema describing the output of the AXAMD channels command, a mapping of channel numbers to names
type: object
patternProperties:
        '^ch[0-9]+$':
                description: Channel number and name
                type: string
```


* **Error Response:**

ref Error Responses

error types

  * internal-server-error
  * missing-api-key
  * bad-api-key
  * broken-api-key
  * bad-request

* **Sample Call:**

  `wget --header 'X-API-Key: <elided>' $AXAMD_SERVER/v1/sra/channels`

### Anomaly List

* **URL**

  `/v1/sra/anomalies`

* **METHOD**

  `GET`

* **Success Response:**

  **Code:** 200  
  **Content:** `{ "dns_match": "Match DNS names anywhere in the DNS label hierarchy." }`

```yaml
id: http://farsightsecurity.com/axamd-anomalies-output-schema#
$schema: http://json-schema.org/draft-04/schema#
title: axamd anomalies output schema
description: Schema describing the output of the AXAMD anomalies command, a mapping of anomaly module names to descriptions
type: object
patternProperties:
        '^ch[0-9]+$':
                description: Anomaly module name and description
                type: string
```

* **Error Response:**

| Error type | Reason |
| --- | --- |
| `internal-server-error` | An internal error has occurred.  Contact support, providing the logid from the response. |
| `missing-api-key` | The X-API-Key header was not provided. |
| `invalid-api-key` | The API key provided does not exist. |
| `broken-api-key` | An internal error has occurred.  Contact support, providing the logid from the response.  |
| `bad-request` | Unable to parse request.  See the reason field in the response for details. |

See Error Responses for more details.

* **Sample Call:**

  `wget --header 'X-API-Key: <elided>' $AXAMD_SERVER/v1/sra/anomalies`

### Stream

* **URL**

  `/v1/sra/stream`

* **METHOD**

  `POST`

* **Data Params**

ref json schema axamd/client/stream-param-schema.yaml

ref AXA Watch Format


* **Successs Response:**

ref Stream Output Formats

* **Error Response:**

| Error type | Reason |
| --- | --- |
| `internal-server-error` | An internal error has occurred.  Contact support, providing the logid from the response. |
| `missing-api-key` | The X-API-Key header was not provided. |
| `invalid-api-key` | The API key provided does not exist. |
| `broken-api-key` | An internal error has occurred.  Contact support, providing the logid from the response.  |
| `bad-request` | Unable to parse request.  See the reason field in the response for details. |

See Error Responses for more details.

* **Sample Call:**

  `wget --data '{ "channels"=[212], "watches"=["ch=212"] }' --header 'X-API-Key: <elided>' $AXAMD_SERVER/v1/sra/anomalies`

  `wget --data '{ "anomalies"={ "module"="dns_match", "watches"=["dns=*."], "options"="match=example.com" } }' --header 'X-API-Key: <elided>' $AXAMD_SERVER/v1/sra/anomalies`

### AXA JSON Messages

### Error Responses

Per draft-ietf-appsawg-http-problem-03

all responses have:
  * `type`
  * `title`
  * `status`
  * `logid`

many responses have:
  * `detail`

All types based `https://www.farsightsecurity.com/axamd/problems`

  * `internal-server-error`
  * `missing-api-key`
  * `bad-api-key`
  * `broken-api-key`
    * `api-key`
  * `bad-request`
    * `reason`
  * `sra-not-enabled`
  * `rad-not-enabled`
  * `connection-error`
  * `channel-not-found`
    * `channel`
  * `channel-error`
    * `channel`
  * `watch-error`
    * `channel`
    * `anomaly` (in rad mode)
  * `anomaly-not-found`
    * `anomaly`
  * `anomaly-error`
    * `anomaly`
  * `rate-limit-error`
    * `limit`
    * `report-interval`
  * `sample-rate-error`
    * `rate`
