import unittest

from nxtool.log_providers import flat_file
from nxtool.whitelists_generators import cookies


class TestParseLog(unittest.TestCase):
    def test_show_stats(self):
        parser = flat_file.FlatFile()
        parser.get_statistics()

    def test_generate_whitelist(self):
        parser = flat_file.FlatFile('./tests/data/cookies.txt')
        self.assertEqual(cookies.generate_whitelist(parser, []), [{'wl': [42000227], 'mz':['$HEADERS_VAR:cookie']}])
        self.assertEqual(cookies.generate_whitelist(parser, [{'wl': [42000227]}]), [])
