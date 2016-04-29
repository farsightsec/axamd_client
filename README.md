# Farsight Advanced Exchange Access (AXA) RESTful Interface

The Farsight AXA RESTful Interface adds a streaming HTTP interface on top of the
[AXA toolkit](https://www.github.com/farsightsec/axa) to enable developers of
web-based applications to interface with Farsight's SRA (SIE Remote Access)
and RAD (Realtime Anomaly Detector) servers.

Access is controlled via an API key that is passed as the `X-API-Key` HTTP
header.

## Advanced Exchange Access (AXA)
AXA is an in-house developed binary protocol for the real-time transit of
Security Information Exchange (SIE) traffic.

## SIE Remote Access (SRA)
SRA is Farsight Security's bespoke remote access service for SIE traffic.
It transits SIE datagrams through an encrypted tunnel to the customer's network.
More detail including client tool and C library downloads can be found at
the [AXA git repository](https://www.github.com/farsightsec/axa).

## Realtime Anomaly Detector (RAD)
RAD is the daughter service to SRA offering custom, server-side filtering of
SIE data through the use of in-house developed "RAD Modules". With RAD,
customers have access to complex filtering modules that provide services
like real-time detection of DNS record corruption and brand infringement
campaigns. RAD toolware is also available at the [AXA git repository](https://www.github.com/farsightsec/axa).

## AXA Watch Format
To signify interest in a particular SIE channel, IP address, or domain,
AXA uses the concept of "watches". These are summarized below:

| Watch Type  | Syntax                      | Notes                                                                                                                                           |
| ----------- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| Channel     | `ch=<#>`                    | Enable "all watch" for specified SIE channel number. Not supported in RAD mode.                                                                 |
| IP Address  | `ip=<ipv4 or ipv6 literal>` | Watch IP-based SIE traffic containing specified IP address. In CIDR notation.                                                                   |
| Domain Name | `dns=<domain>`              | Watch DNS-based SIE traffic containing specified domain name. Supports wildcards such as `*.` or `*.example.com`, but not `www.*` or `*.host.*` |

## Python Reference Implementation
Install `axamd_client` as per the following:

```
# python setup.py install
```

A full-featured client is installed as `axamd_client`.  You may configure the
client using `/etc/axamd-client.conf`, `~/.axamd-client.conf`, or any file you
specify on the command line.  You may forego this and use only command line
options if you prefer.  Configuration files are YAML or JSON objects.
Allowable keys are:

| Option | Type | Description |
| --- | --- | --- |
| `server` | string | URI to AXAMD server |
| `apikey` | string | Key for authentication |
| `proxy` | string | HTTP proxy |
| `timeout` | number | Socket timeout in seconds |
| `sample-rate` | number | Channel sampling rate (percent) |
| `rate-limit` | integer | Maximum packets per second |
| `report-interval` | integer | Seconds between emission of server accounting messages (packet statistics) |

See [client-config-schema.yaml](axamd/client/client-config-schema.yaml) for more details.

The client can be invoked from the command line as follows:

```
usage: axamd_client [-h] [--config CONFIG] [--server SERVER] [--apikey APIKEY]
                 [--proxy PROXY] [--timeout TIMEOUT] [--rate-limit PPS]
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
  --proxy PROXY, -p PROXY
                        HTTP proxy
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

The client may also be used programmatically.  It is compatible with both
Python 2 and Python 3.  The client raises `axamd.ProblemDetails` exceptions
from server errors corresponding to the internet draft
[draft-ietf-appsawg-http-problem-03](https://tools.ietf.org/html/draft-ietf-appsawg-http-problem-03).  For full details, invoke:

```
$ pydoc axamd.client
```

Example usage:

```python
from axamd.client import Client, Anomaly
import json

apikey = '00000000-0000-0000-0000-00000000'
c = Client('https://axamd.sie-remote.net', apikey)

for line in c.sra(channels=[212], watches=['ch=212']):
    data = json.loads(line)

# or

import nmsg

# detect the string "mail" anywhere in the DNS label hierarchy
for line in c.rad(anomalies=[Anomaly('string_match', ['dns=*.'], 'match=mail')],
        output_format='nmsg+json'):
    msg = nmsg.message.from_json(line)
```

While the distribution has several python dependencies, `axamd.client.Client`
only depends on the Python requests module.  Schema validation for parameters
is enabled if the `PyYAML` and `jsonschema` modules are available.

## Protocol

The Farsight AXA RESTful Interface consists of four methods.  Two of the
methods, "Channel List" and "Anomaly List," are used to interrogate the server
about which channels and anomaly modules the user is allowed to access.  The
remaining methods, "SRA Stream" and "RAD Stream," stream line-delimited
JSON (or binary nmsg container, if requested) data per JSON-encoded parameters
sent in a POST request.

The server reports problems using the protocol defined in the
[Problem Reports for HTTP APIs](https://tools.ietf.org/html/draft-ietf-appsawg-http-problem-03)
internet draft.  See the Error Responses section for a detailed listing of
all problem codes.

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

| Error type              | Reason                                                                                    |
| ----------------------- | ----------------------------------------------------------------------------------------- |
| `internal-server-error` | An internal error has occurred.  Contact support, providing the `logid` from the response.  |
| `missing-api-key`       | The X-API-Key header was not provided.                                                    |
| `invalid-api-key`       | The API key provided does not exist.                                                      |
| `broken-api-key`        | An internal error has occurred.  Contact support, providing the `logid` from the response.  |
| `bad-request`           | Unable to parse request.  See the reason field in the response for details.               |

See Error Responses for more details.

* **Sample Call:**

  `wget --header 'X-API-Key: <elided>' $AXAMD_SERVER/v1/sra/channels`

### Anomaly List

* **URL**

  `/v1/rad/anomalies`

* **METHOD**

  `GET`

* **Success Response:**

  **Code:** 200  
  **Content:** `{ "string_match": "Watch for strings anywhere in the DNS label hierarchy." }`

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

| Error type              | Reason                                                                                    |
| ----------------------- | ----------------------------------------------------------------------------------------- |
| `internal-server-error` | An internal error has occurred.  Contact support, providing the `logid` from the response.  |
| `missing-api-key`       | The X-API-Key header was not provided.                                                    |
| `invalid-api-key`       | The API key provided does not exist.                                                      |
| `broken-api-key`        | An internal error has occurred.  Contact support, providing the `logid` from the response.  |
| `bad-request`           | Unable to parse request.  See the reason field in the response for details.               |

See Error Responses for more details.

* **Sample Call:**

  `wget --header 'X-API-Key: <elided>' $AXAMD_SERVER/v1/rad/anomalies`

### SRA Stream

* **URL**

  `/v1/sra/stream`

* **METHOD**

  `POST`

* **Data Params**

This method takes a JSON or YAML document conforming to the
[SRA Stream Parameters JSON Schema](axamd/client/sra-stream-param-schema.yaml).

| Field Name | Type | Required | Description |
| --- | --- | --- | --- |
| `channels` | array[integer] | Yes | Channel numbers to enable. |
| `watches` | array[string] | Yes | Watch strings. |
| `sample_rate` | number | No | Sampling rate (float over (0..1]) for the SRA server. |
| `rate_limit` | integer | No | Maximum watch hits per second. |
| `report_interval` | integer | No | Seconds between statistics messages. |
| `output_format` | string | No |  One of `axa+json`, `nmsg+json`, or `nmsg+binary`. |

See the AXA Watch Format for more details on watch syntax.

* **Successs Response:**

See the Stream Output Formats section.

* **Error Response:**

| Error type              | Reason                                                                                    |
| ----------------------- | ----------------------------------------------------------------------------------------- |
| `internal-server-error` | An internal error has occurred.  Contact support, providing the `logid` from the response.  |
| `missing-api-key`       | The X-API-Key header was not provided.                                                    |
| `invalid-api-key`       | The API key provided does not exist.                                                      |
| `broken-api-key`        | An internal error has occurred.  Contact support, providing the `logid` from the response.  |
| `bad-request`           | Unable to parse request.  See the reason field in the response for details.               |

See Error Responses for more details.

* **Sample Call:**

  `wget --data '{ "channels"=[212], "watches"=["ch=212"] }' --header 'X-API-Key: <elided>' $AXAMD_SERVER/v1/sra/stream`

### RAD Stream

* **URL**

  `/v1/rad/stream`

* **METHOD**

  `POST`

* **Data Params**

This method takes a JSON or YAML document conforming to the
[RAD Stream Parameters JSON Schema](axamd/client/rad-stream-param-schema.yaml).

| Field Name | Type | Required | Description |
| --- | --- | --- | --- |
| `anomalies` | object(`module`, `watches`, `options`) | Yes | Anomaly module definitions. |
| .. `module` | string | Yes | Anomaly module name. |
| .. `watches` | array[string] | Yes | Watch strings |
| .. `options` | string | No | Anomaly module options. |
| `sample_rate` | number | No | Sampling rate (float over (0..1]) for the SRA server. |
| `rate_limit` | integer | No | Maximum watch hits per second. |
| `report_interval` | integer | No | Seconds between statistics messages. |
| `output_format` | string | No |  One of `axa+json`, `nmsg+json`, or `nmsg+binary`. |

See the AXA Watch Format for more details on watch syntax.

* **Successs Response:**

See the Stream Output Formats section.

* **Error Response:**

| Error type              | Reason                                                                                    |
| ----------------------- | ----------------------------------------------------------------------------------------- |
| `internal-server-error` | An internal error has occurred.  Contact support, providing the `logid` from the response.  |
| `missing-api-key`       | The X-API-Key header was not provided.                                                    |
| `invalid-api-key`       | The API key provided does not exist.                                                      |
| `broken-api-key`        | An internal error has occurred.  Contact support, providing the `logid` from the response.  |
| `bad-request`           | Unable to parse request.  See the reason field in the response for details.               |

See Error Responses for more details.

* **Sample Call:**

  `wget --data '{ "anomalies"={ "module"="string_match", "watches"=["dns=*."], "options"="match=www" } }' --header 'X-API-Key: <elided>' $AXAMD_SERVER/v1/rad/stream`

### Stream Output Formats

You may specify any of three output formats for the two stream commands.
The default, `axa+json`, is the native AXA format and supports all messages.
The two nmsg formats only support watch and anomaly hits and do not include
status messages at this time.

#### AXA JSON Messages

This is the default message format.  Output consists of line-delimited,
JSON-encoded AXA protocol strings.  It can be explicitly requested using
the parameter `output_format=axa+json`.

Each protocol message contains the following fields:

| Field Name | Type | Description |
| --- | --- | --- |
| tag | "\*" or integer | Associates this message with a watch or anomaly module |
| op | string | Specifies which type of message this is. |

For [tags](https://github.com/farsightsec/axa#axa-message-header),
"\*" is for tagless messages, such as statistics. Otherwise, the
tag number corresponds to the index of the watch or anomaly in the stream
parameters, plus one.

The following example describes how watches are assigned for SRA streams:

```json
{
   "watches": [
       "ip=192.0.2.0/24",
       "ip=198.51.100.0/24",
   ]
}
```

The watch `ip=192.0.2.0/24` is assigned tag 1 and the watch
`ip=198.51.100.0/24` is assigned tag 2.

The following example describes how watches are assigned for RAD streams:

```json
{
    "anomalies": [
        {
           "module": "ip_probe",
	   "watches": [
	       "ip=192.0.2.0/24",
	       "ip=198.51.100.0/24",
	   ]
        },
        {
           "module": "ip_probe",
	   "watches": [
	       "ip=203.0.113.0/24",
	   ]
        }
    ]
}
```

The watches `ip=192.0.2.0/24` and `ip=198.51.100.0/24` are assigned tag 1, and
`ip=203.0.113.0/24` is assigned tag 2.

There are four AXA op codes that are of interest to a user of the RESTful
interface:  MISSED and WATCH HIT for SRA users, RAD MISSED and ANOMALY HIT for
RAD users.

 * **MISSED**

| Field Name | Type | Description |
| --- | --- | --- |
| `missed` | integer | The number of packets (SIE messages or raw IP packets) lost in the network between the source and the SRA server or dropped by the SRA server because it was too busy. |
| `dropped` | integer | The number of packets dropped by SRA client-server congestion. |
| `rlimit` | integer | The number of packets dropped by rate limiting. |
| `filtered` | integer | The total number of packets considered. |
| `last_report` | integer | The UNIX epoch of the previous report. |

 * **WATCH HIT (nmsg)**

This is the watch hit that you will most often see.  It is fired when SRA
matches your watch against a nmsg message.

| Field Name | Type | Description |
| --- | --- | --- |
| `channel` | string | The channel number (ch#) on which this hit was observed. |
| `nmsg` | object | The JSON-encoded nmsg object.  See NMSG JSON Messages. |
| `field` or `field_idx` | string or integer | The nmsg field (or index)that triggered this watch hit. |
| `val_idx` | integer | The value index within the nmsg field that triggered this watch hit. |
| `vname` or `vid` | string or integer | The NMSG vendor name (or ID). |
| `mname` or `msgtype` | string or integer | The NMSG module name (or ID). |
| `time` | string | Timestamp when the NMSG message was reported. |

 * **WATCH HIT (ip)**

You will see this watch hit type when SRA matches your watch against an IP
packet on an IP-only channel (such as the darknet channel).

| Field Name | Type | Description |
| --- | --- | --- |
| `channel` | string | The channel number (ch#) on which this hit was observed. |
| `af` | string or integer | The address family of `src` and `dst`. |
| `src` | string | Source address. |
| `dst` | string | Destination address. |
| `ttl` | int | IP time to live. |
| `payload` | string | base64-encoded packet payload. |
| `proto` | string | Network protocol. |
| `src_port` | integer | Network protocol src port. |
| `dst_port` | integer | Network protocol dst port. |
| `flags` | array[string] | TCP flags. |
| `time` | string | Timestamp when the IP packet was captured. |

TCP flags are any of `SYN`, `FIN`, `ACK`, `RST`.

 * **RAD MISSED**

| Field Name | Type | Description |
| --- | --- | --- |
| `sra_missed` | integer | The number of packets (SIE messages or raw IP packets) lost in the network between the source and the SRA server or dropped by the SRA server because it was too busy. |
| `sra_dropped` | integer | The number of packets dropped by SRA client-server congestion. |
| `sra_rlimit` | integer | The number of packets dropped by rate limiting by the SRA server. |
| `sra_filtered` | integer | The total number of packets considered by the SRA server. |
| `dropped` | integer | The number of packets dropped by RAD client-server congestion. |
| `rlimit` | integer | The number of packets dropped by RAD rate limiting. |
| `filtered` | integer | The total number of packets considered by RAD modules. |
| `last_report` | integer | The UNIX epoch of the previous report |

 * **Anomaly Hit**

Anomaly hits have all of the same fields of nmsg and IP watch hits, plus the
following:

| Field Name | Type | Description |
| --- | --- | --- |
| `an` | string | Module that detected the anomaly. |

Please consult the [AXA json schema](axamd/client/axa-json-schema.yaml) for full
details about every protocol message type. Please do not use this schema to
validate input. It is very large and computationally expensive to validate.

#### NMSG JSON Messages

The `nmsg+json` output format is useful if you intend to use the AXA RESTful
interface solely as a tranport protocol for nmsg messages.  Messages can be
loaded directly using the `nmsg_message_from_json` function (or
`nmsg.message.from_json` in Python). It is requested using the parameter
`output_format=nmsg+json`.

| Field Name | Type | Description |
| --- | --- | --- |
| `mname` | string | Module name. |
| `vname` | string | Vendor name. |
| `time` | string | Time when the message was recorded. |
| `message` | object | Module-specific fields. |

#### NMSG Binary Messages

The `nmsg+binary` output format is plumbing for a future nmsg input type.  It
is not intended for use at this time but its contents are serialized nmsg
containers.  It can be requested using `output_format=nmsg+binary`.

### Error Responses

The AXA RESTful interface implements the IETF draft [draft-ietf-appsawg-http-problem-03](https://tools.ietf.org/html/draft-ietf-appsawg-http-problem-03)
for all error responses.  All responses have the following fields:

| Field | Description |
| --- | --- |
| `type` | The problem type.  See below. |
| `title` | Human-readable title. |
| `detail` | Human-readable error details. (optional) |
| `status` | HTTP status code. |
| `logid` | UUID identifying this transaction in log messages. Provide this to support for all problem-related queries. |

#### Problem Types

All problem types below have the URI base
`https://www.farsightsecurity.com/axamd/problems`.  It is omitted for brevity.

| Identifier | Description |
| --- | --- |
| `internal-server-error` | An internal error has occurred. Please contact support, providing the `logid`. |
| `missing-api-key` | The X-API-Key header was not included in the request. |
| `invalid-api-key` | The API Key is not provisioned. |
| `broken-api-key` | An internal authentication error has occurred. Please contact support, providing the `logid`. Has an `api-key` field containing the damaged API key. |
| `bad-request` | The request URI, method, or parameters are invalid.  See the `reason` field for an explanation. |
| `sra-not-enabled` | SIE Remote Access is not enabled for this account. |
| `rad-not-enabled` | Realtime Anomaly Detector is not enabled for this account. |
| `connection-error` | There was an internal error connecting to the SRA or RAD server.  Please contact support, providing the `logid`. |
| `channel-not-found` | The channel requested either does not exist or is not provisioned for this account. See the `channel` field for the channel number that caused the problem. |
| `channel-error` | The SRA server returned an error when a channel was requested.  See `detail` for a human-readable error message and the `channel` field for which channel caused the error. |
| `watch-error` | The SRA or RAD server returned an error when a watch was requested.  See `detail` for a human-readable error message. The `anomaly` field is populated in RAD mode with the anomaly module that the watch is connected with and the `watch` field for which watch caused the error. |
| `anomaly-not-found` | The anomaly module requested either does not exist or is not provisioned for this account.  See the `anomaly` field for the anomaly module name that caused the problem. |
| `anomaly-error` | The RAD server returned an error when an anomaly was requested.  See `detail` for a human-readable error message and `anomaly` for which anomaly module caused the error. |
| `rate-limit-error` | The SRA or RAD server returned an error when setting the rate limit or report-interval.  See the `detail` field for a human-readable error message and the `limit` or `report-interval` fields for the rate limit or report interval that caused the issue. |
| `sample-rate-error` | The SRA or RAD server returned an error when setting the sample rate.  See `detail` for a human-readable error message. The invalid sample rate is included in the `rate` field. |
