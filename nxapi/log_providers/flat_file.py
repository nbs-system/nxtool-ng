import collections

from nxapi import log_parsers
from nxapi.log_providers import LogProvider


class FlatFile(LogProvider):
    def __init__(self, fname='./tests/data/logs.txt'):
        self.logs = list()
        self.filters = collections.defaultdict(list)
        with open(fname) as f:
            for line in f:
                log = log_parsers.parse_log(line)
                if log:
                    self.logs.append(log)

    def _get_top(self, field, size=250):
        ret = dict()
        values = (log[1][field] for log in self.__get_filtered_logs())
        for key, value in collections.Counter(values).most_common(10):
            ret[key] = value
        return ret

    def __get_filtered_logs(self):
        """
        yield the loglines accordingly to the filtering policy defined in `self.filters`
        """
        if not self.filters:  # we don't filter, give everything!
            for log in self.logs:
                yield log
        else:
            for log in self.logs:
                for key, value in log[1].items():
                    if key in self.filters:  # are we filtering on this `key`?
                        if value in self.filters[key]:  # is the current `value` in the filtering list?
                            yield log

    def get_results(self):
        pass

    def add_filters(self, filters):
        """
        :param dict filters: What fields/values do we want to filter on?
        """
        for key, value in filters.items():
            self.filters[key].append(value)

