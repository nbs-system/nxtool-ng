from . import modify_search
from nxapi import whitelist


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
    for _, _, r in map(whitelist.parse, whitelists):
        if 'HEADERS:Cookie' in r['mz']:
            already_whitelisted_id.union(r['wl'])
    wid = [wid for wid in data if wid not in already_whitelisted_id]

    return list() if not wid else ['BasicRule wl:%s "mz:$HEADERS_VAR:cookie";' % ','.join(wid), ]
