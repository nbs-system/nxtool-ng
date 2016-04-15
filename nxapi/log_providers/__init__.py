class LogProvider(object):
    def add_filters(self, filters):
        raise NotImplementedError

    def get_results(self):
        raise NotImplementedError

    def get_statistics(self):
        raise NotImplementedError