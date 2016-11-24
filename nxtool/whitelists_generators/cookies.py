import logging

from nxapi.rules import get_description_core
from . import modify_search


@modify_search
def generate_whitelist(provider, whitelists):
    """
    Generate whitelists for exceptions that are happening in the cookies.

    :param provider:
    :param list whitelists:
    :return list of dict:
    """
    logging.info('Generating \033[1mcookies\033[0m rules')

    for rule in whitelists:
        provider.add_filters({'id': rule.get('wl', '*'), 'mz': rule.get('mz', '*')}, negative=True)

    provider.add_filters({'zone': 'HEADERS', 'var_name': 'cookie'})

    # We don't require the hits to be spread across users, because the cookie might be only available
    # to admins for example. But since the browser sends it on every request, it should be
    # spread amongst urls.
    data = provider.get_relevant_ids(['uri'])

    ret = list()
    for _id in data:
        ret.append(
            {
                'mz': ['$HEADERS_VAR:cookie'],
                'wl': [_id],
                'msg': 'Cookies that matches a %s' % get_description_core(_id)
            }
        )
    return ret