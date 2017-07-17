import re
class LogProvider(object):
    def __init__(self, auto_commit_limit=400):
        self.nlist = list()
        self.auto_commit = auto_commit_limit
        self.total_objs = 0
        self.total_commits = 0
        self.simplified_uri = False

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

    def insert(self, obj):
        """ This function adds the object obj to the instance of LogProvider.
        :param obj: object to add to this instance
        :return bool: Success ?
        """
        self.nlist.extend(obj)
        if self.auto_commit > 0 and len(self.nlist) > self.auto_commit:
            return self.commit()
        return True

    def commit(self):
        """ This function commits pendants objects in the LogProvider instance

        """
        raise NotImplementedError

    def simplify_uri(self, uri):
        """ This function simplify the uri representation to loosen constraints on whitelist generation
        :param uri:
        :return:
        """
        t = dict()
        for key, value in uri.items():
            new_key = re.sub('([a-zA-Z]+)', 'A', key)
            new_key = re.sub('([0-9]+)', 'N', new_key)
            if new_key in t:
                t[new_key] += value
            else:
                t[new_key] = value
        return t

    def stop(self):
        self.commit()
    
