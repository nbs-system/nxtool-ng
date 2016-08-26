import logging

from . import modify_search


@modify_search
def generate_whitelist(provider, whitelists):
    """

    :param provider:
    :return:
    """
    logging.info('Generating \033[1mGoogle analytics\033[0m rules')
    cookies_names = ['__utma', '__utmb', '__utmc', '__utmt', '__utmv', '__utmz']
    provider.add_filters({'zone': 'ARGS', 'var_name': cookies_names})
    data = provider.get_relevant_ids(['uri', 'ip'])

    # Filter already whitelisted things
    already_whitelisted_id = set()
    for r in whitelists:
        if 'mz' not in r or any(cookie_name in r['mz'] for cookie_name in cookies_names):
            already_whitelisted_id = already_whitelisted_id.union(r['wl'])
    wid = [wid for wid in data if wid not in already_whitelisted_id]

    return list() if not wid else [{'mz': ['$ARGS_VAR_X:__utm[abctvz]'], 'wl': wid, 'msg': 'Google analytics'}, ]
