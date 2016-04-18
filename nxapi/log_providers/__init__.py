class LogProvider(object):
    def add_filters(self, filters):
        """
        :param dict filters: What fields/values do we want to filter on?
        """
        raise NotImplementedError

    def get_results(self):
        raise NotImplementedError

    def get_statistics(self):
        raise NotImplementedError
