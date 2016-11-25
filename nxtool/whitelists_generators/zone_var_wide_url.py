import logging
import collections

from nxapi.rules import get_description_core
from . import modify_search


@modify_search
def generate_whitelist(provider, whitelists):
    """
    Generate rules for a specific variable, in a specific zone, on a specific url.
    :param log_provider.elastic provider:
    :return:
    """
    logging.info('Generating \033[1mvar + zone + url\033[0m rules')
    res = collections.defaultdict(lambda: collections.defaultdict(dict))

    for rule in whitelists:
        provider.add_filters({'id': rule.get('wl', '*'), 'mz': rule.get('mz', '*')}, negative=True)

    for uri in provider.get_top('uri').keys():
        _search = provider.export_search()
        provider.add_filters({'uri': uri})

        for zone in ['ARGS', 'BODY', 'ARGS|NAME', 'BODY|NAME']:
            logging.debug('Searching for arguments in the zone \033[1m%s\033[0m on the url \033[1m%s\033[0m', zone, uri)

            provider.add_filters({'zone': zone})
            data = provider.get_top('var_name')

            for var_name, nb in data.items():
                if not var_name:
                    continue
                elif nb < 1000:
                    logging.debug('Discarding the argument \033[32m%s\033[0m (%d occurrences)', var_name, nb)
                    continue
                search = provider.export_search()
                provider.add_filters({'var_name': var_name})
                res[uri][zone][var_name] = provider.get_relevant_ids(['ip'])
                provider.import_search(search)

        provider.import_search(_search)

    ret = list()
    for uri, content in res.items():
        for zone, _content in content.items():
            if not _content:  # We don't care about empty sets
                continue
            for var_name, __ids in _content.items():
                if not __ids:
                    continue
                descriptions = ', or a '.join(map(get_description_core, __ids))
                if zone.endswith('|NAME'):
                    mz = '%s:%s|%s' % (zone.split('|')[0], var_name, 'NAME')
                else:
                    mz = '$%s_VAR:%s' % (zone, var_name)
                ret.append(
                    {'mz': ['$URL:%s|%s' % (uri, mz)], 'wl': __ids,
                     'msg': 'Variable zone-wide on a specific url if it matches a %s' % descriptions}
                )
    return ret
