import logging
import collections

from . import modify_search


@modify_search
def generate_whitelist(provider, whitelists):
    """

    :param log_provider.elastic provider:
    :return:
    """
    logging.info('Generating \033[1mvar + zone\033[0m rules')
    res = collections.defaultdict(lambda: collections.defaultdict(dict))

    for rule in whitelists:
        provider.add_filters({'id': rule.get('wl', '*'), 'mz': rule.get('mz', '*')}, negative=True)

    uris = provider.get_top('uri')
    for uri in uris.keys():
        _search = provider.export_search()
        provider.add_filters({'uri': uri})
        for zone in ['ARGS', 'BODY', 'ARGS|NAME', 'BODY|NAME']:
            logging.debug('Searching for arguments in the zone \033[1m%s\033[0m', zone)
            search = provider.export_search()
            provider.add_filters({'zone': zone})
            data = provider.get_top('var_name')
            provider.import_search(search)

            for var_name, nb in data.items():
                if not var_name:
                    continue
                elif nb < 1000:
                    logging.debug('Discarding the argument \033[32m%s\033[0m (%d occurrences)', var_name, nb)
                    continue
                search = provider.export_search()
                provider.add_filters({'zone': zone, 'var_name': var_name})
                # every peer should have triggered the exception
                res[uri][zone][var_name] = provider.get_relevant_ids(['ip'])
                provider.import_search(search)
        provider.import_search(_search)

    if not res:
        return list()

    ret = []
    for uri, content in res.items():
        for zone, _content in content.items():
            if not _content:  # We don't care about empty sets
                continue
            for var_name, __content in _content.items():
                if not __content:
                    continue
                if zone.endswith('|NAME'):
                    mz = '%s:%s|%s' % (zone.split('|')[0], var_name, 'NAME')
                else:
                    mz = '$%s_VAR:%s' % (zone, var_name)
                ret.append(
                    {'mz': [mz + '|$URL:%s' % uri], 'wl': __content, 'msg': 'Variable zone-wide on a specific url'}
                )
    return ret
