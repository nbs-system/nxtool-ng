import unittest

from nxtool.log_providers import elastic


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
        parser.search.scan = lambda : None
        parser.add_filters({'pif': 'paf'})
        filters = parser.get_filters()
        parser.get_results()
        self.assertEqual(parser.get_filters(), filters)