class LogProvider(object):
    def add_filters(self, filters):
        """
        :param dict filters: What fields/values do we want to filter on?
        """
        raise NotImplementedError

    def get_results(self):
        raise NotImplementedError

    def get_statistics(self):
        ret = dict()
        for field in ['uri', 'server', 'ip']:
            ret[field] = self._get_top(field)
        return ret

    def _get_top(self, field, size=250):
        raise NotImplementedError
