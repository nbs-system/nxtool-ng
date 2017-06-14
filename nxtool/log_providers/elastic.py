from __future__ import print_function
import logging
import operator
import collections
import hashlib
import json
import datetime

from functools import partial

try:  # Fuck you guido for removing reduce
    # noinspection PyUnresolvedReferences
    from functools import reduce
except ImportError:
    pass

try:
    from ConfigParser import SafeConfigParser as ConfigParser
except ImportError:  # python3
    from configparser import ConfigParser

from elasticsearch_dsl import Search, Q
from elasticsearch_dsl.connections import connections

from nxtool.log_providers import LogProvider


class Elastic(LogProvider):
    def __init__(self, config_file='config.cfg'):
        super(Elastic, self).__init__()

        self.percentage=10.0
        self.minimum_occurrences=250
        
        config = ConfigParser({'host': '127.0.0.1', 'use_ssl': True, 'index': 'nxapi', 'version': 2})

# The ConfigParser documentation points out that there's no way to force defaults config option
# outside the "DEFAULT" section.
        config = ConfigParser()
        config.read(config_file)
        if not config.has_section('elastic'):
            config.add_section('elastic')
        
        for option, value in {'use_ssl': 'True', 'host': '127.0.0.1', 'version': '2', 'index': 'nxapi', 'doc_type': 'events'}.items():
            if not config.has_option('elastic', option):
                config.set('elastic', option, value)

        self.version = config.getint('elastic', 'version')
        self.index = config.get('elastic', 'index')
        use_ssl = config.getboolean('elastic', 'use_ssl')
        host = config.get('elastic', 'host')
        self.doc_type = config.get('elastic', 'doc_type')
        
        self.client = connections.create_connection(hosts=[host], use_ssl=use_ssl, index=self.index, version=self.version, timeout=30, retry_on_timeout=True )
        self.initialize_search()

    def initialize_search(self):
        self.search = Search(using=self.client, index=self.index, doc_type=self.doc_type).extra(size=10000)
        
    def export_search(self):
        return self.search

    def import_search(self, search):
        self.search = search

    def get_filters(self):
        return self.search.to_dict()

    def add_filters(self, filters, regexp=False, negative=False):
        """
        Add `filters` to the query.
         `filters is a dict of the form {'field': value, field2: value2}, but you can also use a list of values
         instead of a `str`. They'll be added as a _or_ (and not a _and_).
        :param dict filters:
        :param bool regexp:
        :param bool negative:
        :return:
        """
        # We need to use multi_match, since we get the fields names dynamically.
        for key, value in filters.items():
            if isinstance(value, set):
                value = list(value)

            # There is no need to process empty values.
            if not value:
                continue

            if isinstance(value, list):
                if negative:
                    self.search = self.search.query(Q('bool', must_not=[
                        reduce(operator.or_, [Q('multi_match', query=v, fields=[key]) for v in value])])
                    )
                else:
                    self.search = self.search.query(Q('bool', must=[
                        reduce(operator.or_, [Q('multi_match', query=v, fields=[key]) for v in value])])
                    )
            else:
                if negative:
                    self.search = self.search.query(~Q("multi_match", query=value, fields=[key]))
                else:
                    self.search = self.search.query(Q("multi_match", query=value, fields=[key]))

    def get_top(self, field, size=250):
        """
        Get the top values for the given `field`
        :param str field: the field to filter on
        :param int size: how many top values to return, top
        :return dict of int: A structure of the form {value: number_of_hits, value2: numer_of_hits2}
        """
        search = self.search
        ret = dict()
        self.search = self.search.params(search_type="count")
        self.search.aggs.bucket('TEST', 'terms', field=field)
        for hit in self.search.execute(ignore_cache=True).aggregations['TEST']['buckets']:
            ret[hit['key']] = hit['doc_count']
        self.search = search
        return ret

    def get_relevant_ids(self, fields, percentage=0, minimum_occurrences=0):
        """ This function is supposed to return the id that are reparteed/present on the `fields`.

         :param list of str fields:
         :param float percentage:
         :param float minimum_occurrences:
         :return set of int:
         """
        minimum_occurences = minimum_occurrences or self.minimum_occurrences
        percentage = percentage or self.percentage

        ret = set()
        search = self.search
        ids = set(int(i['id']) for i in self.search.execute())  # get all possible ID
        self.search = search

        for _id in ids:
            search = self.search

            self.add_filters({'id': _id})

            # Get how many different fields there are for a given `id`
            data = collections.defaultdict(set)
            fields_counter = collections.defaultdict(int)
            for res in self.search.execute():
                for field in fields:
                    if res[field] not in data[field]:
                        fields_counter[field] += 1.0
                    data[field].add(res[field])

            # Ignore id that are present on less than 10% of different values of each fields
            for field, content in data.items():
                if len(content) < minimum_occurrences:
                    logging.debug('Discarding id \033[32m%s\033[0m only present %d times.', _id, len(content))
                    continue
                _percentage = len(content) / fields_counter[field] * 100.0
                if _percentage > percentage:
                    continue
                logging.debug('Discarding id \033[32m%s\033[0m present in %d%% of different values of the \033[32m%s\033[0m field', _id, _percentage, field)
                break
            else:
                ret.add(_id)
            self.search = search

        return ret

    def reset_filters(self):
        self.search = Search(using=self.client, index=self.index, doc_type=self.doc_type).extra(size=10000)

    def get_results(self):
        """
        Return a `Result` object obtained from the execution of the search `self.search`.
        :return Result: The `Result` object obtained from the execution of the search `self.search`.
        """
        search = self.search
        result = self.search.scan()
        self.search = search
        return result

    def commit(self):
        """Process list of dict (yes) and push them to DB """
        self.total_objs += len(self.nlist)
        count = 0
        full_body = ""
        items = []
        for entry in self.nlist:
            items.append({"index" : {
                "_index": self.index,
                "_type" : "events"}})
            entry['whitelisted'] = "false"
            entry['comments'] = "import:"+str(datetime.datetime.now())
            # go utf-8 ?
            for x in entry.keys():
                if isinstance(entry[x], basestring):
                    entry[x] = unicode(entry[x], errors='replace')
            items.append(entry)
            count += 1
        try:
            self.client.bulk(body=items)
        except TransportError:
            for meta, item in zip(items[0::2], items[1::2]): #We build tuples in items (items[0], items[1]), (items[2], items[3]) ...
                self.client.bulk(body=[meta, item])

        self.total_commits += count
        logging.debug("Written "+str(self.total_commits)+" events")
        del self.nlist[0:len(self.nlist)]

