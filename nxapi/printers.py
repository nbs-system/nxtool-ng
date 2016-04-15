"""
Helper functions to display data on stdout
"""


def print_statistics(results):
    for key, value in results.items():
        print key
        print '\n'.join('%s: %s' % (i,j) for i,j in value.items()) + '\n'


def print_generic(results):
    for item in results.hits:
        print '\n'.join('%s: %s' % (k, item[k]) for k in item) + '\n'
