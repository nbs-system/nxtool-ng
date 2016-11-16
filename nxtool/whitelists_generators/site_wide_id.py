import logging

from . import modify_search


@modify_search
def generate_whitelist(provider, whitelists):
    """

    :param log_provider.elastic provider:
    :return:
    """
    logging.info('Generating \033[1msite\033[0m rules')
    zones = provider.get_top('zone')

    for rule in whitelists:
        provider.add_filters({'id': rule.get('wl', '*'), 'mz': rule.get('mz', '*')}, negative=True)

    ret = dict()
    for zone in zones.keys():
        logging.debug('Generating \033[1murl_wide_id\033[0m rules for \033[1m%s\033[0m', zone)
        search = provider.export_search()
        provider.add_filters({'zone': zone})
        data = provider.get_relevant_ids(['zone'], 75)
        provider.import_search(search)

        if data:
            ret[zone] = data

    return list() if not ret else [{'mz': [zone], 'wl': _id, 'msg': 'Site-wide id+zone'} for zone, _id in ret.items()]

