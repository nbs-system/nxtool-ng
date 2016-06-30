import logging
import collections

from . import modify_search


@modify_search
def generate_whitelist(provider, whitelists):
    """

    :param log_provider.elastic provider:
    :return:
    """
    logging.info('Running \033[1murl_wide_id\033[0m')
    res = collections.defaultdict(dict)

    search = provider.export_search()
    provider.add_filters({'zone': 'ARGS'})
    data = provider.get_top('var_name')
    provider.import_search(search)

    for var_name, nb in data.items():
        if nb < 1000 or not var_name:
            logging.debug('Discarding url argument \033[32m%s\033[0m (%d occurrences)', var_name, nb)
            continue
        search = provider.export_search()
        provider.add_filters({'zone': 'ARGS', 'var_name': var_name})
        res[var_name] = provider.get_relevant_ids(['ip'])  # every peer should have triggered the exception
        provider.import_search(search)

    # # Filter already whitelisted things
    # already_whitelisted_id= set()
    # for r in whitelists:
    #     for i in r['wl']:
    #         already_whitelisted_id.add(i)
    # wid = [wid for wid in data.values() if wid not in already_whitelisted_id]

    return list() if not res else [{'mz' : ['ARGS:%s' % arg], 'wl': _id, 'msg': 'URL argument'} for arg,_id in res.items()]

