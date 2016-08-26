"""
Helper functions to display data on stdout
"""


def print_statistics(results):
    for key, value in results.items():
        print('# \033[100m%s\033[0m #' % key.upper())
        print('\n'.join('\033[32m%s\033[0m: \033[1m%s\033[0m' % (i, j) for i, j in value.items()) + '\n')


def print_generic(results):
    if hasattr(results, 'hits'):
        it = results.hits
    else:
        it = results
    for item in it:
        print('\n'.join('%s: %s' % (k, item[k]) for k in item) + '\n')
