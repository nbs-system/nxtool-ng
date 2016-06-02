class LogProvider(object):
    def add_filters(self, filters):
        """
        :param dict filters: What fields/values do we want to filter on?
        """
        raise NotImplementedError

    def get_results(self):
        raise NotImplementedError

    def get_statistics(self):
        """ Get some events statistics

        :return a dict of dict of int:
        """
        ret = dict()
        for field in ['uri', 'server', 'ip', 'zone']:
            ret[field] = self.get_top(field)
        return ret

    def get_top(self, field, size=250):
        """ Get the top values on a given `field`.

        :param str field: On what field we want to filter
        :param int size: On how much data do we want to process
        :return dict of str: {field: nb_occurences, ..}
        """
        raise NotImplementedError
