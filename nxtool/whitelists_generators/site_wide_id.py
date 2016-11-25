import logging

from nxapi.rules import get_description_core
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

    res = dict()
    for zone in zones.keys():
        logging.debug('Generating \033[1murl_wide_id\033[0m rules for \033[1m%s\033[0m', zone)
        search = provider.export_search()
        provider.add_filters({'zone': zone})
        data = provider.get_relevant_ids(['zone'], 75)
        provider.import_search(search)

        if data:
            res[zone] = data

    ret = list()
    for zone, _id in res.items():
        ret.append({
            'mz': [zone],
            'wl': _id,
            'msg': 'Site-wide id+zone if it matches %s' % ', or a '.join(map(get_description_core, _id))}
        )
    return ret


