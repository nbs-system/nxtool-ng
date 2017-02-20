import logging

from . import modify_search


def __check_and_strip_brackets(string):
    """ Return `False` if the `string` variable hasn't the same number of opening and closing brackets,
    else, return the variable without the trailing brackets: `pouet[1[2]3]` -> `pouet`

    :param str string:
    :return bool|int:
    """
    if sum(1 if char == '[' else -1 if char == ']' else 0 for char in string) != 0:
        return False
    try:
        return string[:string.index('[')]
    except ValueError:  # no '[' nor ']' in the `string`
        return False


@modify_search
def generate_whitelist(provider, whitelists):
    """
    Generate whitelists for variables that look like an array, eg. `pouet[1]`, `pouet[1[2]3]`, or `pouet[1][2]`.

    :param provider: The data provider
    :param list whitelist: Already generated rules, acting as a whitelist
    :return list of dict: The generated whitelists
    """
    ids = [1310, 1311]  # [ and ]

    logging.info('Generating \033[1marray-like variable name\033[0m rules')

    provider.add_filters({'zone': ['ARGS|NAME', 'BODY|NAME'], 'id': ids})
    variables = provider.get_top('var_name')

    ret = list()  # we can't use a `set` for `ret`, because we're using `dict` with it, and they're unhashable.
    stripped_names = set()  # so we don't add duplicate rules
    for var_name, nb in variables.items():
        if nb < 1000:
            logging.debug('Discarding the variable \033[32m%s\033[0m (%d occurrences)', var_name, nb)
            continue

        stripped_name = __check_and_strip_brackets(var_name)
        if not stripped_name:
            logging.debug('The variable \033[32m%s\033[0m does not have an expected form', var_name)
            continue

        if stripped_name not in stripped_names:
            stripped_names.add(stripped_name)
            ret.append({
                'mz': ['$BODY_VAR_X:^%s\[.+\]$' % stripped_name],
                'wl': ids, 'msg': 'Array-like variable name'})
            ret.append({
                'mz': ['$ARGS_VAR_X:^%s\[.+\]$' % stripped_name],
                'wl': ids, 'msg': 'Array-like variable name'})
    return ret
