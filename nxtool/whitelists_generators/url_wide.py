import logging
import collections

from . import modify_search


@modify_search
def generate_whitelist(provider, whitelists):
    """

    :param log_provider.elastic provider:
    :return:
    """
    logging.info('Running \033[1mzone_wide_id\033[0m')
    uris = provider.get_top('uri')

    res = collections.defaultdict(set)
    for uri in uris.keys():
        logging.info('Searching for id in the uri \033[1m%s\033[0m', uri)
        search = provider.export_search()
        provider.add_filters({'uri': uri, 'zone': 'URL'})
        data = provider.get_top('id')
        provider.import_search(search)

        for id_name, nb in data.items():
            if not id_name:
                continue
            elif nb < 1000:
                logging.debug('Discarding the argument \033[32m%s\033[0m (%d occurrences)', id_name, nb)
                continue
            else:
                logging.debug('\033[1mKeeping\033[0m the id \033[32m%s\033[0m (%d occurrences)', id_name, nb)
            search = provider.export_search()
            provider.add_filters({'uri': uri, 'id': id_name})
            if int(id_name) in provider.get_relevant_ids(['ip']):
                res[uri].add(id_name)
            provider.import_search(search)

    #TODO filter already whitelisted things

    if not res:
        return list()

    ret = []
    for uri, content in res.items():
        ret.append({'mz': ['$URL:%s' % (uri,)], 'wl': content, 'msg': 'url-wide ID whitelist'})
    return ret
