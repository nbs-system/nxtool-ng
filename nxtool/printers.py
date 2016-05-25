"""
Helper functions to display data on stdout
"""


def print_statistics(results):
    for key, value in results.items():
        print('# \033[95m%s\033[0m #' % key.upper())
        print('\n'.join('\033[91m%s\033[0m: %s' % (i, j) for i, j in value.items()) + '\n')


def print_generic(results):
    if hasattr(results, 'hits'):
        it = results.hits
    else:
        it = results
    for item in it:
        print('\n'.join('%s: %s' % (k, item[k]) for k in item) + '\n')
