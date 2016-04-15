import argparse
import sys
import shlex

import urllib3
urllib3.disable_warnings()

from nxapi import printers
from nxapi.log_providers import elastic, flat_file


def __filter(source, filters, hostname=''):
    _filter = {}

    if filters:
        for param in filters.split(','):
            try:
                key, value = param.split('=')
            except ValueError:
                print('Parameters should be of the form key=value,key2=value2,...')
                return
            _filter[key] = value

    if hostname:
        _filter['server'] = hostname

    source.add_filters(_filter)


def __create_argparser():
    """ Create a simple arguments parser. """
    parser = argparse.ArgumentParser(description='Sweet tool to help you managing your naxsi logs.')

    parser.add_argument('hostname', action='store', nargs='?')

    log_sources = parser.add_argument_group('Log sources')
    log_sources.add_argument('--elastic', action='store_true')
    log_sources.add_argument('--flat_file', action='store_true')

    actions = parser.add_argument_group('Actions')
    actions.add_argument('--typing', action='store_true')
    actions.add_argument('--whitelist', action='store_true')
    actions.add_argument('--filter', action='store')
    actions.add_argument('--stats', action='store_true')

    return parser.parse_args()


def main():
    args = __create_argparser()

    if args.elastic is True:
        source = elastic.Elastic()
    elif args.flat_file is True:
        source = flat_file
    else:
        print('Please give me a source.')
        return 1

    __filter(source, args.filter, args.hostname)  # Filtering can be used for any operation

    if args.stats:
        printers.print_statistics(source.get_statistics())
    else:
        print printers.print_generic(source.get_results())


if __name__ == '__main__':
    sys.exit(main())