import logging
import collections

from . import modify_search


#TODO

@modify_search
def generate_whitelist(provider, whitelists):
    """

    :param log_provider.elastic provider:
    :return:
    """
    logging.info('Running \033[1murl_wide_id\033[0m')
    zones = provider.get_top('zone')

    ret = dict()
    for zone in zones.keys():
        logging.debug('Generating \033[1murl_wide_id\033[0m rules for \033[1m%s\033[0m' % zone)
        search = provider.export_search()
        provider.add_filters({'zone': zone})
        data = provider.get_relevant_ids(['zone'], 75)
        provider.import_search(search)

        if data:
            if any(zone in r['mz'] and set(r['zl']) & set(data) for r in whitelists):
                continue
            ret[zone] = data

    return list() if not ret else [{'mz' : [zone], 'wl': _id, 'msg': 'Site-wide id+zone'} for zone, _id in ret.items()]

