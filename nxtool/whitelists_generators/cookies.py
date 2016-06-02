import logging

from . import modify_search


@modify_search
def generate_whitelist(provider, whitelists):
    """

    :param provider:
    :return:
    """
    provider.add_filters({'zone': 'HEADERS', 'var_name': 'cookie'})
    data = provider.get_relevant_ids(['uri', 'peer'])

    # Filter already whitelisted things
    already_whitelisted_id = set()
    for r in whitelists:
        if 'HEADERS:Cookie' in r['mz']:
            already_whitelisted_id.union(r['wl'])
    wid = [int(wid) for wid in data if wid not in already_whitelisted_id]

    return list() if not wid else [{'mz': ['$HEADERS_VAR:cookie'], 'wl': wid}, ]
