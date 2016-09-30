import logging

from . import modify_search


def __check_and_strip_brackets(string):
    """ Return `False` if the `string` variable hasn't the same number of opening and closing brackets,
    else, return the variable without the trailing brackets: `pouet[1[2]3]` -> `pouet`

    :param str string:
    :return bool|int:
    """
    if sum(1 if char == '[' else -1 if char == ']' else 0 for char in string):
        return False
    return string[:string.index('[')]


@modify_search
def generate_whitelist(provider, whitelists):
    """

    :param provider:
    :return:
    """
    ids = [1310, 1311]  # [ and ]

    logging.info('Generating \033[1marray-like variable name\033[0m rules')
    search = provider.export_search()

    provider.add_filters({'zone': ['ARGS|NAME', 'BODY|NAME'], 'id': ids})
    variables = provider.get_top('var_name')
    provider.import_search(search)

    ret = set()
    for var_name, nb in variables:
        if nb < 1000:
            logging.debug('Discarding the variable \033[32m%s\033[0m (%d occurrences)', var_name, nb)
            continue

        stripped_name = __check_and_strip_brackets(var_name)
        if not stripped_name:
            logging.debug('The variable \033[32m%s\033[0m does not have an expected form', var_name, nb)
            continue
        ret.add({
            'mz': ['$BODY_VAR_X:%s\[.+\]' % stripped_name, '$ARGS_VAR_X:%s\[.+\]' % stripped_name],
            'wl': ids, 'msg': 'Array-like variable name'})

    return list(ret)
