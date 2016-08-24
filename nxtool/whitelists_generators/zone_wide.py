import logging
import collections

from . import modify_search


@modify_search
def generate_whitelist(provider, whitelists):
    """

    :param log_provider.elastic provider:
    :return:
    """
    logging.info('Running \033[1mzone_wide_id\033[0m')
    res = collections.defaultdict(dict)

    for zone in ['ARGS', 'BODY']:
        logging.info('Searching for aguments in the zone \033[1m%s\033[0m', zone)
        search = provider.export_search()
        provider.add_filters({'zone': zone})
        data = provider.get_top('id')
        provider.import_search(search)

        for id_name, nb in data.items():
            if not id_name:
                continue
            elif nb < 1000:
                logging.debug('Discarding the argument \033[32m%s\033[0m (%d occurrences)', id_name, nb)
                continue
            search = provider.export_search()
            provider.add_filters({'zone': zone, 'id': id_name})
            res[zone][id_name] = provider.get_relevant_ids(['ip'])  # every peer should have triggered the exception
            provider.import_search(search)

    #TODO filter already whitelisted things

    if not res:
        return list()

    ret = []
    
    for zone, content in res.items():
        for id_name in content.keys():
            ret.append({'mz': ['%s' % (zone,)], 'wl': [id_name], 'msg': 'zone-wide ID whitelist'})
    return ret
