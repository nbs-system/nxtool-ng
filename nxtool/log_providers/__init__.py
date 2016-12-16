class LogProvider(object):
    def add_filters(self, filters, regexp=False, negative=False):
        """
        :param dict filters: What fields/values do we want to filter on?
        :param bool regexp: Treat `filters` as regexp ?
        :param bool negative: Shall the match be negative ?
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
        :return dict of str: {field: nb_occurrences, ..}
        """
        raise NotImplementedError

    def get_relevant_ids(self, fields, percentage=10.0, minimum_occurrences=250):
        """ This function is supposed to return the id that are reparteed/present on the `fields`.

        :param str fields:
        :param float percentage:
        :param int minimum_occurrences:
        :return set:
        """
        raise NotImplementedError
