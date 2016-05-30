from __future__ import print_function
import math
import logging
import operator

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
        self.search = Search(using=self.client, index='nxapi', doc_type='events')

    def reset_filters(self):
        self.search = Search(using=self.client, index='nxapi', doc_type='events')

    def add_filters(self, filters):
        # We need to use multi_match, since we get the fields names dynamically.
        for key, value in filters.items():
            if isinstance(value, list):
                self.search = self.search.query(
                    reduce(operator.or_, [Q('multi_match', query=v, fields=[key]) for v in value])
                )
            else:
                self.search = self.search.query(Q("multi_match", query=value, fields=[key]))

    def _get_top(self, field, size=250):
        ret = dict()

        self.search = self.search.params(search_type="count")
        self.search.aggs.bucket('TEST', 'terms', field=field)
        for hit in self.search.execute().aggregations['TEST']['buckets']:
            nb_hits = str(hit['doc_count'])
            ret[nb_hits] = hit['key']

        return ret

    def get_relevant_ids(self, fields):
        """
         We want to keep alerts that are spread over a vast number of different`fields`

            To measure the spreading, we're using this metric: https://en.wikipedia.org/wiki/Coefficient_of_variation
        :param list of str fields:
        :return:
        """
        search = self.search
        ids = list()

        self.search.aggs.bucket('ids', 'terms', field='id', size=250)
        for field in fields:
            self.search.aggs['ids'].bucket(field + 's', 'terms', field=field, size=10)

        result = self.search.execute()
        id_buckets = result.aggregations['ids'].buckets
        for id_bucket in id_buckets:
            for field in fields: # FIXME if an ID is unevenly reparteed, ditch it.
                s0, s1, s2 = 0.0, 0.0, 0.0
                for uri in id_bucket.__getattr__(field + 's').buckets:
                    s0 += 1.0
                    s1 += uri['doc_count']
                    s2 += uri['doc_count'] * uri['doc_count']
                if s0 < 10:
                    logging.debug('The id %s is present in %d %s, classifying it as non-significant.', id_bucket.key,
                                  s0, field)
                    continue

                try:  # magic formula to compute the coefficient of variation
                    std_dev = math.sqrt((s0 * s2 - s1 * s1) / (s0 * (s0 - 1)))
                    std_dev /= (s1 / s0)
                    std_dev *= 100
                except ZeroDivisionError:
                    std_dev = 0.0
                if std_dev < 10:  # 10% of deviation max
                    logging.debug('The id %s appeared on %d %s, with a coefficient of variation of %d%%.',
                                  id_bucket.key, s0, field, std_dev)
                    continue
            ids.append(id_bucket.key)

        self.search = search
        ret = dict()
        for _id in ids:
            self.add_filters({'id': _id})
            answer = self.search.execute()
            ret[_id] = answer.hits.hits
            self.search = search

        self.search = search
        return ret

    def _get_results(self):
        """
        Return a `Result` object obtained from the execution of the search `self.search`.
        This method has a side effect: it re-initialize `self.search`.
        :return Result: The `Result` object obtained from the execution of the search `self.search`.
        """
        result = self.search.scan()
        self.search = Search(using=self.client, index='nxapi', doc_type='events')
        return result

