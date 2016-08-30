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
    res = collections.defaultdict(dict)

    for rule in whitelists:
        provider.add_filters({'id': rule.get('wl', '*'), 'mz': rule.get('mz', '*')}, negative=True)

    for zone in ['ARGS', 'BODY', 'ARGS|NAME', 'BODY|NAME']:
        logging.debug('Searching for aguments in the zone \033[1m%s\033[0m', zone)
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
            res[zone][var_name] = provider.get_relevant_ids(['ip'])  # every peer should have triggered the exception
            provider.import_search(search)

    if not res:
        return list()

    ret = []
    for zone, content in res.items():
        for variable, ids in content.items():
            ret.append({'mz': ['%s:%s' % (zone, variable)], 'wl': ids, 'msg': 'Variable'})
    return ret
