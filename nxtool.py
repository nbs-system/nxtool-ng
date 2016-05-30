import argparse
import sys
import logging

import urllib3
urllib3.disable_warnings()

from nxtool import printers
from nxtool.log_providers import flat_file
from nxtool.whitelists_generators import cookies, images_1002

try:
    from nxtool.log_providers import elastic
    elastic_imported = True
except ImportError:
    print('Unable to correctly import the elastic material. Did you forget to install elasticsearch-dsl?')
    elastic_imported = False


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
    parser.add_argument('--verbose', action='store_true')

    log_sources = parser.add_argument_group('Log sources')
    log_sources.add_argument('--elastic', action='store_true')
    log_sources.add_argument('--flat-file', action='store_true')
    log_sources.add_argument('--stdin', action='store_true')
    log_sources.add_argument('--archive', action='store_true')

    actions = parser.add_argument_group('Actions')
    actions.add_argument('--typing', action='store_true')
    actions.add_argument('--whitelist', action='store_true')
    actions.add_argument('--filter', action='store')
    actions.add_argument('--stats', action='store_true')

    return parser.parse_args()


def main():
    args = __create_argparser()

    if args.verbose:
        logging.getLogger("elasticsearch").setLevel(logging.ERROR)
        logging.getLogger("urllib3").setLevel(logging.ERROR)
        logging.basicConfig(level=logging.DEBUG)

    if args.elastic is True:
        if elastic_imported is False:
            print('You asked for an elastic source, but you do not have the required dependencies.')
            return
        source = elastic.Elastic()
    elif args.flat_file is True:
        source = flat_file.FlatFile()
    elif args.stdin is True:
        source = flat_file.FlatFile(None)
    else:
        print('Please give me a valid source.')
        return 1

    __filter(source, args.filter, args.hostname)  # Filtering can be used for any operation

    if args.stats:
        printers.print_statistics(source.get_statistics())
    elif args.whitelist:
        print(cookies.generate_whitelist(source))
        print(images_1002.generate_whitelist(source))
    else:
        print(printers.print_generic(source._get_results()))


if __name__ == '__main__':
    sys.exit(main())
