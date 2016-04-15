import collections

from nxapi import log_parsers
from nxapi.log_providers import LogProvider


class FlatFile(LogProvider):
    def __init__(self, fname='./tests/data/logs.txt'):
        self.logs = list()
        with open(fname) as f:
            for line in f:
                self.logs.append(log_parsers.parse_log(line))

    def get_statistics(self):
        ret = collections.defaultdict(dict)
        for field in ['uri', 'server', 'ip']:
            values = (log[1][field] for log in self.logs)
            for key, value in collections.Counter(values).most_common(10):
                ret[field][key] = value
        return ret

    def get_results(self):
        pass

    def add_filters(self, filters):
        pass

