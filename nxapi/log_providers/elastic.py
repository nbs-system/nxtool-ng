import ConfigParser

from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search, Q


class Elastic(object):
    def __init__(self, config_file='config.cfg'):
        config = ConfigParser.SafeConfigParser()  # TODO add default values
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
