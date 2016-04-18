try:
    from ConfigParser import SafeConfigParser as ConfigParser
except ImportError:  # python3
    from configparser import ConfigParser

import collections

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q

from nxapi.log_providers import LogProvider


class Elastic(LogProvider):
    def __init__(self, config_file='config.cfg'):
        config = ConfigParser({'host': '127.0.0.1', 'use_ssl': True, 'index': 'nxapi', 'version': 2})
        config.read(config_file)

        version = config.getint('elastic', 'version')
        index = config.get('elastic', 'index')
        use_ssl = config.getboolean('elastic', 'use_ssl')
        host = config.get('elastic', 'host')

        self.client = Elasticsearch([host, ], use_ssl=use_ssl, index=index, version=version)
        self.search = Search(using=self.client, index='nxapi', doc_type='events')

    def add_filters(self, filters):
        """
        :param dict filters: What fields/values do we want to filter on?
        """
        for key, value in filters.items():
            # We need to use multi_match, since we get the fields names dynamically.
            self.search = self.search.query(Q("multi_match", query=value, fields=[key]))

    def get_results(self):
        """
        Return a `Result` object obtained from the execution of the search `self.search`.
        This method has a side effect: it re-initialize `self.search`.
        :return Result: The `Result` object obtained from the execution of the search `self.search`.
        """
        result = self.search.execute()
        self.search = Search(using=self.client, index='nxapi', doc_type='events')
        return result

    def get_statistics(self):
        ret = collections.defaultdict(dict)

        for field in ['uri', 'server', 'zone', 'ip']:
            self.search = self.search.params(search_type="count")
            self.search.aggs.bucket('TEST', 'terms', field=field)

            for hit in self.search.execute().aggregations['TEST']['buckets']:
                nb_hits = str(hit['doc_count'])
                ret[field][nb_hits] = hit['key']
        self.search = None

        return ret
