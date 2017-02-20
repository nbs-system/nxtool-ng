import logging
import collections

from nxapi.rules import get_description_core
from . import modify_search


@modify_search
def generate_whitelist(provider, whitelists):
    """

    :param log_provider.elastic provider:
    :return:
    """
    logging.info('Generating \033[1mvar + zone\033[0m rules')
    res = collections.defaultdict(dict)

    for zone in ['ARGS', 'BODY', 'ARGS|NAME', 'BODY|NAME']:
        logging.debug('Searching for arguments in the zone \033[1m%s\033[0m', zone)
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
            res[zone][var_name] = provider.get_relevant_ids(['ip'])  # every peer should have triggered the exception
            provider.import_search(search)

    ret = list()
    for zone, content in res.items():
        for variable, ids in content.items():
            if not ids:  # We don't care about empty sets
                continue
            descriptions = ', or a '.join(map(get_description_core, ids))
            if zone.endswith('|NAME'):
                mz = '%s:%s|%s' % (zone.split('|')[0], variable, 'NAME')
            else:
                mz = '%s:%s' % (zone, variable)
            ret.append({'mz': [mz], 'wl': ids, 'msg': 'Variable zone-wide if it matches a %s' % descriptions})
    return ret
