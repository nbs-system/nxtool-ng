import logging
import collections

from nxapi.rules import get_description_core
from . import modify_search


@modify_search
def generate_whitelist(provider, whitelists):
    """

    :param log_provider.elastic provider:
    :param list of dict whitelists:
    :return:
    """
    logging.info('Generating \033[1mzone\033[0m rules')
    zones = provider.get_top('zone')

    for rule in whitelists:
        provider.add_filters({'id': rule.get('wl', '*'), 'mz': rule.get('mz', '*')}, negative=True)

    res = collections.defaultdict(set)
    for zone in zones.keys():
        logging.debug('Searching for id in the zone \033[1m%s\033[0m', zone)
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
            if int(id_name) in provider.get_relevant_ids(['ip']):
                res[zone].add(id_name)
            provider.import_search(search)

    ret = list()
    for zone, wid in res.items():
        ret.append(
            {
                'mz': ['%s' % (zone,)],
                'wl': wid,
                'msg': 'zone-wide ID whitelist if it matches a %s' % ', or a '.join(map(get_description_core, wid))}
        )
    return ret
