from . import modify_search

@modify_search
def generate_whitelist(provider):
    provider.add_filters({'zone': 'URL', 'id': '1002'})
    data = provider.get_relevant_ids(['uri', 'peer'])
    return 'BasicRule Wl:%s "mz:FIXME";' % ','.join(data.keys())
