import logging

from . import modify_search


@modify_search
def generate_whitelist(provider, whitelists):
    """

    :param provider:
    :return:
    """
    logging.info('Generating \033[1mcookies\033[0m rules')
    provider.add_filters({'zone': 'HEADERS', 'var_name': 'cookie'})
    #data = provider.get_relevant_ids(['uri', 'ip'])
    data = provider.get_relevant_ids(['uri'])

    # Filter already whitelisted things
    already_whitelisted_id = set()
    for r in whitelists:
        if 'mz' not in r or'HEADERS:Cookie' in r['mz']:
            already_whitelisted_id = already_whitelisted_id.union(r['wl'])
    wid = sorted([wid for wid in data if wid not in already_whitelisted_id])

    return list() if not wid else [{'mz': ['$HEADERS_VAR:cookie'], 'wl': wid, 'msg': 'Cookies'}, ]
