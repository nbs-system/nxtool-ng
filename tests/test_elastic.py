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
