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

from __future__ import print_function

import argparse
import errno
import logging
import os
import sys
import textwrap
import re

from . import __version__
from .client import Anomaly, Client
from .exceptions import ProblemDetails
import jsonschema
import option_merge
import pkg_resources
import yaml
import signal

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


def duration_handler(signum, frame):
    """
    this is called if the --duration parameter is specified
    """
    if signum == signal.SIGALRM:
        sys.exit(0)


def timespec_to_seconds(ts):
    """
    turn either hh:mm:ss or %dw%dd%dh%dm%ds
    into seconds. for the latter, things like "1w" or "1w1s" are
    ok, but "1s1w" (out-of-order) is not.
    :param ts: string timespec
    :return: integer seconds
    """
    c = {'w': 0, 'd': 0, 'h': 0, 'm': 0, 's': 0}

    try:
        c['h'], c['m'], c['s'] = map(abs, map(int, ts.split(":")))
    except:
        m = re.search('(?P<weeks>[0-9]*)(w?)(?P<days>[0-9]*)(d?)(?P<hours>[0-9]*)(m?)(?P<minutes>[0-9]*)(m?)(?P<seconds>[0-9]*)(s?)',ts)
        if m and len(m.group()) > 0:
            a = []
            for i in m.groups():
                if i != '': a.append(i)
            if len(a) % 2: return None
            c.update({a[i+1]: abs(int(a[i])) for i in range(0, len(a), 2)})
        else:
            return None

    return c['w'] * 604800 + \
           c['d'] * 86400  + \
           c['h'] * 3600   + \
           c['m'] * 60     + c['s']


def main():
    parser = argparse.ArgumentParser(
            description='Client for the AXA RESTful Interface')
    parser.add_argument('--config', '-c', help='Path to config file')
    parser.add_argument('--number', '-n',
                        type=int,
                        help='Return no more than N json messages and stop')
    parser.add_argument('--duration', '-d',
                        help='Run for hh:mm:ss (or #w#d#h#m#s) duration and then stop.')
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
    if args.duration:
        stoptime = timespec_to_seconds(args.duration)
        if stoptime is None:
            parser.error('Duration must be specified as hh:mm:ss or #w#d#h#m#s')
        signal.signal(signal.SIGALRM, duration_handler)
    if args.number:
        if args.number < 0:
            parser.error('Number parameter must be greater than zero')
        config['number'] = args.number
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
            for channel, chan_dict in client.list_channels(timeout=timeout).items():
                if not isinstance(chan_dict, dict):
                    desc = chan_dict # backward compat where axamd would return desc directly
                else:
                    try:
                        desc = chan_dict['description']
                    except KeyError:
                        desc = "No description available."

                if sys.stdout.isatty():
                    print('{}:\n\t{}'.format(channel, "\n\t".join(textwrap.wrap(desc))))
                else:
                    print('{}: {}'.format(channel, desc))

        elif args.list_anomalies:
            for module, mod_dict in client.list_anomalies(timeout=timeout).items():
                if not isinstance(mod_dict, dict):
                    desc = mod_dict # backward compat where axamd would return desc directly
                else:
                    try:
                        desc = mod_dict['description']
                    except KeyError:
                        desc = "No description available."

                if sys.stdout.isatty():
                    print('{}:\n\t{}'.format(module, "\n\t".join(textwrap.wrap(desc))))
                else:
                    print('{}: {}'.format(module, desc))
        elif args.channels:
            count = 0
            if args.duration: signal.alarm(stoptime)
            for result in client.sra(args.channels, args.watches,
                    timeout=timeout, **client_args):
                print (result)
                sys.stdout.flush()
                count += 1
                if args.number and count >= args.number:
                    break
        elif args.anomaly:
            count = 0
            anomaly = Anomaly(args.anomaly[0], watches=args.watches,
                    options=' '.join(args.anomaly[1:]))
            if args.duration: signal.alarm(stoptime)
            for result in client.rad([anomaly], timeout=timeout, **client_args):
                print (result)
                sys.stdout.flush()
                count += 1
                if args.number and count >= args.number:
                    break
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
