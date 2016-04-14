
def generate_statistics(source):
    for key, value in source.get_statistics().items():
        print key
        print '\n'.join('%s: %s' % (i,j) for i,j in value.items()) + '\n'