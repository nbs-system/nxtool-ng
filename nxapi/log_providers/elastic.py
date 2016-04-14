import ConfigParser
import collections

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q, A, aggs


class Elastic(object):
    def __init__(self, config_file='config.cfg'):
        config = ConfigParser.SafeConfigParser({'host': '127.0.0.1', 'use_ssl': True, 'index': 'nxapi', 'version': 2})
        config.read(config_file)

        version = config.getint('elastic', 'version')
        index = config.get('elastic', 'index')
        use_ssl = config.getboolean('elastic', 'use_ssl')
        host = config.get('elastic', 'host')

        self.client = Elasticsearch([host, ], use_ssl=use_ssl, index=index, version=version)

    def get_filtered(self, hostname, filters):
        """
        :param str hostname: The hostname got get intel on
        :param dict filters: What fields/values do we want to filter on?
        :return:
        """
        s = Search(using=self.client, index='nxapi', doc_type='events').query('match', server=hostname)

        for key, value in filters.items():
            # We need to use multi_match, since we get the fields names dynamically.
            s = s.query(Q("multi_match", query=value, fields=[key]))

        return s.execute()

    def get_statistics(self, interval=3600):
        ret = collections.defaultdict(dict)

        for field in ['uri', 'server', 'zone', 'ip']:
            s = Search(using=self.client, index='nxapi', doc_type='events')
            s = s.params(search_type="count")
            s.aggs.bucket('TEST', 'terms', field=field)

            for hit in s.execute().aggregations['TEST']['buckets']:
                ret[field][str(hit['doc_count'])] = hit['key']

        return ret