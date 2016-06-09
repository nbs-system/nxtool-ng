from __future__ import print_function
import logging
import operator
import collections

try:  # Fuck you guido for removing reduce
    from functools import reduce
except ImportError:
    pass

try:
    from ConfigParser import SafeConfigParser as ConfigParser
except ImportError:  # python3
    from configparser import ConfigParser

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, MultiSearch

from nxtool.log_providers import LogProvider


class Elastic(LogProvider):
    def __init__(self, config_file='config.cfg'):
        config = ConfigParser({'host': '127.0.0.1', 'use_ssl': True, 'index': 'nxapi', 'version': 2})
        config.read(config_file)

        version = config.getint('elastic', 'version')
        index = config.get('elastic', 'index')
        use_ssl = config.getboolean('elastic', 'use_ssl')
        host = config.get('elastic', 'host')

        self.client = Elasticsearch([host, ], use_ssl=use_ssl, index=index, version=version)
        self.search = Search(using=self.client, index='nxapi', doc_type='events').extra(size=10000)

    def add_filters(self, filters):
        # We need to use multi_match, since we get the fields names dynamically.
        for key, value in filters.items():
            if isinstance(value, list):
                self.search = self.search.query(Q('bool', must=[
                    reduce(operator.or_, [Q('multi_match', query=v, fields=[key]) for v in value])])
                )
            else:
                self.search = self.search.query(Q("multi_match", query=value, fields=[key]))

    def get_top(self, field, size=250):
        ret = dict()

        self.search = self.search.params(search_type="count")
        self.search.aggs.bucket('TEST', 'terms', field=field)
        for hit in self.search.execute().aggregations['TEST']['buckets']:
            nb_hits = str(hit['doc_count'])
            ret[nb_hits] = hit['key']

        return ret

    def get_relevant_ids(self, fields):
        id_blacklist = set()
        ret = set()
        for field in fields:
            stats = collections.defaultdict(int)
            size = 0
            for logline in self.search.execute():
                if logline['id'] not in id_blacklist:
                    stats[logline['id']] += 1
                size += 1.0

            for k, v in stats.items():
                if v / size < 0.10:
                    logging.info('The id %s is present in less than 10%% (%f) of %s : non-significant.', k, v / size, field)
                    id_blacklist.add(k)
                else:
                    ret.add(k)

        return list(ret)

    def reset_filters(self):
        self.search = Search(using=self.client, index='nxapi', doc_type='events').extra(size=10000)

    def get_results(self):
        """
        Return a `Result` object obtained from the execution of the search `self.search`.
        This method has a side effect: it re-initialize `self.search`.
        :return Result: The `Result` object obtained from the execution of the search `self.search`.
        """
        search = self.search
        result = self.search.scan()
        self.search = search
        return result
