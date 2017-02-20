import logging

from . import modify_search


@modify_search
def generate_whitelist(provider, whitelists):
    """
    Generate whitelists for Google Analytics cookies
    :param provider:
    :param list of dict whitelists:
    :return list of dict:
    """
    logging.info('Generating \033[1mGoogle analytics\033[0m rules')

    provider.add_filters({'zone': 'ARGS', 'var_name': ['__utma', '__utmb', '__utmc', '__utmt', '__utmv', '__utmz']})
    ids = provider.get_relevant_ids(['uri', 'ip'])

    ret = list()
    if ids:
        ret.append({'mz': ['$ARGS_VAR_X:__utm[abctvz]'], 'wl': ids, 'msg': 'Google analytics'})
    return ret
