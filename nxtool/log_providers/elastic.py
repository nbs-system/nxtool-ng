from __future__ import print_function
from __future__ import unicode_literals
import logging
import operator
import collections
import datetime

try:  # Fuck you guido for removing reduce
    # noinspection PyUnresolvedReferences
    from functools import reduce
except ImportError:
    pass

try:
    from ConfigParser import SafeConfigParser as ConfigParser
except ImportError:  # python3
    from configparser import ConfigParser

from elasticsearch import TransportError
from elasticsearch_dsl import Search, Q
from elasticsearch_dsl import DocType, Date, Boolean, Integer, Ip, GeoPoint
from elasticsearch_dsl import Index, VERSION
from elasticsearch_dsl.connections import connections

try:
    from elasticsearch_dsl import Text, Keyword
except ImportError:  # oldversion of Elasticsearch
    from elasticsearch_dsl import String
    Text = String
    Keyword = String


from nxtool.log_providers import LogProvider

class Event(DocType):
    ip = Ip()
    coords = GeoPoint()
    learning = Boolean()
    total_processed = Integer()
    total_blocked = Integer()
    blocked = Boolean()
    cscore0 = Keyword()
    score0 = Integer()
    zone = Keyword()
    id = Integer()
    var_name = Keyword()
    date = Date()
    whitelisted = Boolean()
    uri = Text(fields={'raw': Keyword(index = 'not_analyzed')})
    server = Text(fields={'raw': Keyword(index = 'not_analyzed')})
    comments = Text(fields={'raw': Keyword(index = 'not_analyzed')})
    vers = Text(fields={'raw': Keyword(index = 'not_analyzed')})


    class Meta:
        doc_type = 'events'
        ## ToDo change the hardcoded events used when saved is used
        ## elasticsearch_dsl issue 689



class Elastic(LogProvider):
    def __init__(self, config_file='config.cfg'):
        super(Elastic, self).__init__()

        self.percentage=10.0
        self.minimum_occurrences=250
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
        self.client = connections.create_connection(hosts=[host], use_ssl=use_ssl, index=self.index, version=self.version, doc_type=self.doc_type, timeout=30, retry_on_timeout=True )

        Event.init(index=self.index)
        index = Index(self.index, using=self.client)
        index.doc_type(Event)
        self.initialize_search()

    def initialize_search(self):
        self.search = Search(using=self.client, index=self.index).extra(size=10000)
        
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

        if field in ['uri', 'vers', 'comments', 'server']:
            field = ''.join((field, '.raw'))

        if VERSION < (5, 0, 0):
            self.search = self.search.params(search_type='count', default_operator='AND')
        else:
            self.search = self.search.params(search_type='query_then_fetch')
        # This documented at https://elasticsearch-py.readthedocs.io/en/master/api.html#elasticsearch.Elasticsearch.search
        # search_type='count' has been deprecated in ES 2.0
        self.search.aggs.bucket('TEST', 'terms', field=field)
        for hit in self.search.execute(ignore_cache=True).aggregations['TEST']['buckets']:
            ret[hit['key']] = hit['doc_count']
        self.search = search

        if field == 'uri.raw' and self.simplified_uri:
            ret = self.simplify_uri(ret)
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
        ids = set(i['id'] for i in self.search.execute())  # get all possible ID
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
        self.search = Search(using=self.client, index=self.index).extra(size=10000)

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

        def gen_events(events):
            dicts = list()
            for d in events:
                dicts.extend([{'index': {'_index': 'nxapi', '_type': 'events'}}, d.to_dict()])
                yield dicts.pop(-2)
                yield dicts.pop(-1)


        events = list()
        for entry in self.nlist:
            event = Event(_index=self.index)
            for key, value in entry.items():
                setattr(event, key, value)

            event.whitelisted = False
            event.comments = "import on"+str(datetime.datetime.now())
            events.append(event)
            count += 1

        try:
            ret = self.client.bulk(gen_events(events))
            ## ToDo parse ret to selectively loop over events to events.save() whatever happens
        except TransportError as e:
            logging.warning("We encountered an error trying to continue.")
            for event in events:
                event.save(using=self.client)
                ## ToDo find a way to change the hardcoded 'events' for ES doctype
                ## elasticsearch_dsl Issue 689
               
        self.total_commits += count
        logging.debug("Written "+str(self.total_commits)+" events")
        del self.nlist[0:len(self.nlist)]

