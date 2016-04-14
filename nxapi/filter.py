def generate_filter(hostname, filter, source):
    for hit in  source.get_filtered(hostname, filter):
        print hit
