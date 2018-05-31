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

from __future__ import print_function

import argparse
import errno
import logging
import os
import sys

from . import __version__
from .client import Anomaly, Client
from .exceptions import ProblemDetails
import jsonschema
import option_merge
import pkg_resources
import yaml

logger = logging.getLogger(__name__)

_default_config_files=(
    '/etc/axamd-client.conf',
    os.path.expanduser('~/.axamd-client.conf'),
)
DEFAULT_AXAMD_SERVER='https://axamd.sie-network.net'
_default_config = {
    'server': DEFAULT_AXAMD_SERVER,
}

_config_schema = yaml.safe_load(pkg_resources.resource_stream(__name__, 'client-config-schema.yaml'))

def _load_config(filename=None, allow_exceptions=True):
    configs = [ _default_config ]
    config_files = list(_default_config_files)
    config_files = filter(os.path.isfile, config_files)
    if filename:
        config_files.append(filename)

    for config_filename in config_files:
        try:
            new_config = yaml.safe_load(open(config_filename))
        except IOError as e:
            if allow_exceptions and e.errno == errno.EPERM:
                logger.error('{}: {}'.format(config_filename, e.message))
                continue
            raise

        configs.append (new_config)

    config = option_merge.MergedOptions.using(*configs).as_dict()
    jsonschema.validate(config, _config_schema)
    return config

def _percentage(arg):
    v = arg
    if v.endswith('%'):
        v = v[:-1]
    try:
        pct = float(v)
        if pct > 100 or pct < 0:
            raise ValueError
    except ValueError:
        raise argparse.ArgumentTypeError('invalid percentage value: {!r}'.format(arg))

def main():
    parser = argparse.ArgumentParser(
            description='Client for the AXA RESTful Interface')
    parser.add_argument('--config', '-c', help='Path to config file')
    parser.add_argument('--server', '-s', help='AXAMD server')
    parser.add_argument('--apikey', '-k', help='API key')
    parser.add_argument('--proxy', '-p', help='HTTP proxy')
    parser.add_argument('--timeout', '-t', type=float,
            help='Timeout for connections')
    parser.add_argument('--retries', '-R', type=int,
                        help='Number of retries before giving up')
    parser.add_argument('--retry-backoff', '-B', type=float,
                        help='Progressively backoff for each retry')
    parser.add_argument('--rate-limit', '-l', type=int, metavar='PPS',
            help='AXA rate limit')
    parser.add_argument('--report-interval', '-i', type=int, metavar='SECONDS',
            help='AXA report interval')
    parser.add_argument('--sample-rate', '-r', type=_percentage, metavar='PERCENTAGE',
            help='AXA sample rate (percentage)')
    parser.add_argument('--list-channels', action='store_true',
            help='List available channels')
    parser.add_argument('--list-anomalies', action='store_true',
            help='List available anomalies')
    parser.add_argument('--channels', '-C', type=int, nargs='*',
            metavar='CHANNEL',
            help='SRA mode: Channels to listen on')
    parser.add_argument('--watches', '-W', nargs='+',
            metavar='WATCH',
            help='SRA/RAD mode: Watch list')
    parser.add_argument('--anomaly', '-A', nargs='*',
            metavar=('MODULE', 'OPTIONS'),
            help='RAD mode: Anomaly module and options')
    parser.add_argument('--debug', action='store_true', help='Debug mode')
    parser.add_argument('--version', '-V', action='version', version="%(prog)s ({})".format(__version__))
    args = parser.parse_args()

    config = _load_config(args.config)
    if args.server:
        config['server'] = args.server
    if args.apikey:
        config['apikey'] = args.apikey
    if not config.get('apikey'):
        parser.error('API key is not set')
    if args.proxy:
        config['proxy'] = args.proxy
    if args.timeout:
        if args.timeout < 0:
            parser.error('Timeout must be a positive real number')
        config['timeout'] = args.timeout
    if args.retries:
        if args.retries < 0:
            parser.error('Retries must be a positive real number')
        config['retries'] = args.retries
    if args.retry_backoff:
        if args.retry_backoff < 0:
            parser.error('Retry-backoff must be a positive real number')
        config['retry_backoff'] = args.retry_backoff
    if args.rate_limit:
        if args.rate_limit < 0:
            parser.error('Rate limit must be a positive integer')
        config['rate-limit'] = args.rate_limit
    if args.report_interval:
        if args.report_interval < 0:
            parser.error('Report interval must be a positive integer')
        config['report-interval'] = args.report_interval
    if args.sample_rate:
        if args.sample_rate <= 0 or args.sample_rate > 100:
            parser.error('Sample rate must be a real number between (0..100]')
        config['sample-rate'] = args.sample_rate

    if args.channels and args.anomaly:
        parser.error('Channels (SRA mode) and anomaly (RAD mode) are mutually exclusive')

    if not (args.list_channels or args.list_anomalies or args.watches):
        parser.error('A watch list is required unless listing available channels or anomaly modules')

    client = Client(server=config['server'],
                    apikey=config['apikey'],
                    proxy=config.get('proxy'),
                    retries=config.get('retries', 3),
                    retry_backoff=config.get('retry_backoff', 0.3))

    timeout = config.get('timeout')

    client_args = {}
    if 'rate-limit' in config:
        client_args['rate_limit'] = config['rate-limit']
    if 'report-interval' in config:
        client_args['report_interval'] = config['report-interval']
    if 'sample-rate' in config:
        client_args['sample_rate'] = config['sample-rate'] / 100

    try:
        if args.list_channels:
            for channel,description in client.list_channels(timeout=timeout).items():
                print ('{}: {}'.format(channel, description))
        elif args.list_anomalies:
            for module,description in client.list_anomalies(timeout=timeout).items():
                print ('{}: {}'.format(module, description))
        elif args.channels:
            for result in client.sra(args.channels, args.watches,
                    timeout=timeout, **client_args):
                print (result.decode('utf-8'))
                sys.stdout.flush()
        elif args.anomaly:
            anomaly = Anomaly(args.anomaly[0], watches=args.watches,
                    options=' '.join(args.anomaly[1:]))
            for result in client.rad([anomaly], timeout=timeout, **client_args):
                print (result.decode('utf-8'))
                sys.stdout.flush()
        else:
            parser.error('Need channels and watches for SRA mode or anomaly for RAD mode')
    except ProblemDetails as e:
        if args.debug:
            raise
        print ('{}: {}'.format(e.__class__.__name__, e.message), file=sys.stderr)
        return 1
    except Exception as e:
        if args.debug:
            raise
        print ('{}: {}'.format(e.__class__.__name__, str(e)), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return None
    return None

if __name__ == '__main__':
    exit(main())
