from . import modify_search


@modify_search
def generate_whitelist(provider):
    """

    :param provider:
    :return:
    """
    provider.add_filters({'zone': 'HEADERS'})
    data = provider.get_relevant_ids(['uri', 'peer'])
    return 'BasicRule Wl:%s "mz:$HEADERS_VAR:Cookie";' % ','.join(data.keys())