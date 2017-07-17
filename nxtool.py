import argparse
import sys
import logging

from nxapi import whitelist as nxapi_whitelist

from nxtool import printers, typing
from nxtool.log_providers import flat_file
from nxtool.whitelists_generators import cookies, images_1002, google_analytics, zone_var_wide, site_wide_id, zone_wide
from nxtool.whitelists_generators import url_wide, array_like_variables_names, zone_var_wide_url

import urllib3
urllib3.disable_warnings()

WL_MODULES = [google_analytics, images_1002, array_like_variables_names, cookies, zone_var_wide_url, url_wide,
              zone_var_wide, zone_wide, site_wide_id]

try:
    from nxtool.log_providers import elastic
    elastic_imported = True
except ImportError:
    print('Unable to correctly import the elastic material. Did you forget to install elasticsearch-dsl?')
    elastic_imported = False


def __whitelist_from_rules(source, rules):
    """
    :param source:
    :param dict rules:
    """
    for rule in rules:
        whitelist = {'id': rule.get('wl', '*')}
        for matchzone in rule.get('mz', '*')[0].split('|'):
            try:
                zone, value = matchzone.split(':')
            except ValueError:  # no ':', it's a simple matchzone
                whitelist['zone'] = matchzone
                continue

            if zone == '$URL':
                whitelist['url'] = value
            elif zone.startswith('$') and zone.endswith('_VAR'):  # stuff like `$ARGS_VAR:variable_name`
                whitelist['zone'] = zone[1:-4]
                whitelist['var_name'] = value

        source.add_filters(whitelist, regexp=False)


def __filter(source, filters, regexp=False, hostname=''):
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

    source.add_filters(_filter, regexp)


def __create_argparser():
    """ Create a simple arguments parser. """
    parser = argparse.ArgumentParser(description='Sweet tool to help you managing your naxsi logs.')

    parser.add_argument('hostname', action='store', nargs='?')
    parser.add_argument('-v', '--verbose', action='store_true')

    log_sources = parser.add_argument_group('Log sources')
    log_sources.add_argument('--elastic-source', action='store_true')
    log_sources.add_argument('--flat-file', type=str)
    log_sources.add_argument('--stdin', action='store_true')
    log_sources.add_argument('--archive', action='store_true')

    log_destinations = parser.add_argument_group('Log destinations')
    log_destinations.add_argument('--elastic-dest', action='store_true')

    actions = parser.add_argument_group('Actions')
    actions.add_argument('--typing', action='store_true')
    actions.add_argument('--whitelist', action='store_true')
    actions.add_argument('--slack', action='store_true')
    actions.add_argument('--filter', action='store')
    actions.add_argument('--filter-regexp', action='store')
    actions.add_argument('--stats', action='store_true')
    actions.add_argument('--simplify-uri', action='store_true')

    return parser.parse_args()


def main():
    args = __create_argparser()

    logging.getLogger("elasticsearch").setLevel(logging.ERROR)
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, format= '%(message)s')
    else:
        logging.basicConfig(level=logging.INFO, format='[+] %(message)s')

    if args.elastic_source is True:
        if elastic_imported is False:
            print('You asked for an elastic source, but you do not have the required dependencies.')
            return
        source = elastic.Elastic()
    elif args.flat_file:
        source = flat_file.FlatFile(args.flat_file)
    elif args.stdin is True:
        source = flat_file.FlatFile()
    else:
        print('Please give me a valid source (or try to relaunch me with `-h` if you are lost).')
        return 1

    if args.slack and not args.whitelist:
        print('You asked for loosen constraints on whitelist generation but you did''nt ask for whitelist generation.')
        return
    
    # Filtering can be used for any operation
    __filter(source, args.filter, regexp=False, hostname=args.hostname)
    if args.filter_regexp:
        __filter(source, args.filter_regexp, regexp=True, hostname=args.hostname)

    if args.elastic_dest:
        destination = elastic.Elastic()
        for log in source.logs:
            destination.insert([log])
        destination.stop()
    elif args.stats:
        printers.print_statistics(source.get_statistics())
    elif args.whitelist:
        whitelist = list()
        for module in WL_MODULES:
            if args.slack:
                source.minimum_occurences = 0
            if args.simplify_uri:
                source.simplified_uri = True
            rules = module.generate_whitelist(source, whitelist)
            whitelist.extend(rules)
            __whitelist_from_rules(source, rules)
        if whitelist:
            print('\n\033[1mGenerated whitelists:\033[0m')
            print('\t' + ';\n\t'.join(map(nxapi_whitelist.dict_to_str,  whitelist)) + ';')
        else:
            print('\n\033[1mnxtool was not able to generate meaningful whitelist\033[0m')
    elif args.typing:
        printers.print_typed_rules(typing.typification(source))
    else:
        print(printers.print_generic(source.get_results()))


if __name__ == '__main__':
    sys.exit(main())
