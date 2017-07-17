import unittest
import time

from nxtool.log_providers import elastic
from nxtool.log_providers import flat_file

class TestElastic(unittest.TestCase):
    maxDiff = None
    def test_export(self):
        parser = elastic.Elastic()
        search = parser.export_search()
        parser.import_search(parser.export_search())

        self.assertEqual(search, parser.export_search())

    def test_add_filters(self):
        parser = elastic.Elastic()
        parser.add_filters({'pif': 'paf'})
        self.assertEqual(parser.get_filters(), {'query': {'multi_match': {'query': 'paf', 'fields': ['pif']}}, 'size': 10000})

        parser = elastic.Elastic()
        parser.add_filters({'pif': ['paf', 'pouf']})
        self.assertEqual(parser.get_filters(),
                          {'query': {'bool': {'must': [{'bool': {'should':
                              [
                                  {'multi_match': {'fields': ['pif'], 'query': 'paf'}},
                                  {'multi_match': {'fields': ['pif'],'query': 'pouf'}}
                              ]
                          }}]}},'size': 10000})

        parser = elastic.Elastic()
        parser.add_filters({'pif': []})
        self.assertEqual(parser.get_filters(), {'query': {'match_all': {}}, 'size': 10000})

        parser = elastic.Elastic()
        parser.add_filters({'pif': []}, negative=True)
        self.assertEqual(parser.get_filters(), {'query': {'match_all': {}}, 'size': 10000})

        parser = elastic.Elastic()
        parser.add_filters({'pif': set()}, negative=True)
        self.assertEqual(parser.get_filters(), {'query': {'match_all': {}}, 'size': 10000})


        parser = elastic.Elastic()
        parser.add_filters({'pif': [1,]}, negative=True)
        self.assertEqual(parser.get_filters(),  {'query': {'bool': {'must_not': [
            {'multi_match': {'fields': ['pif'],'query': 1}}]}}, 'size': 10000})

        parser = elastic.Elastic()
        parser.add_filters({'pif': 'paf'}, negative=True)
        self.assertEqual(parser.get_filters(), {'query': {'bool':
                                                              {'must_not':
                                                                   [
                                                                       {'multi_match': {'fields': ['pif'], 'query': 'paf'}}
                                                                   ]}},
                                                'size': 10000})

    def test_reset_filters(self):
        parser = elastic.Elastic()
        search = parser.get_filters()
        parser.add_filters({'pif': 'paf'})
        parser.reset_filters()
        self.assertEqual(parser.get_filters(), search)

    def test_get_results(self):
        parser = elastic.Elastic()
        parser.search.scan = lambda: None
        parser.add_filters({'pif': 'paf'})
        filters = parser.get_filters()
        parser.get_results()
        self.assertEqual(parser.get_filters(), filters)

class TestElasticImport(unittest.TestCase):


    def test_elastic_import(self):
        dest = elastic.Elastic()
        source = flat_file.FlatFile('./tests/data/exlog.txt')
        for log in source.logs:
            dest.insert([log])
        dest.stop()
        dest.initialize_search()
        dest.minimum_occurences = 0
        dest.percentage = 0
        time.sleep(5)
        self.assertEqual(dest.get_relevant_ids(['id']), {u'1302', u'42000227'})
        self.assertEqual(dest.get_top('id'), {1302: 3, 42000227: 1})
        self.assertEqual(dest.get_top('uri'), {u'/': 3, u'/phpMyAdmin-2.8.2/scripts/setup.php': 1})
        dest.simplified_uri = True
        self.assertEqual(dest.get_top('uri'), {u'/': 3, u'/A-N.N.N/A/A.A': 1})
        dest.client.indices.delete(index=dest.index, ignore=[400, 404])


