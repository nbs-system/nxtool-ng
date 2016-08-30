import unittest

from nxtool.log_providers import flat_file
from nxtool.whitelists_generators import cookies, images_1002


class TestParseLog(unittest.TestCase):
    def test_show_stats(self):
        parser = flat_file.FlatFile()
        parser.get_statistics()

    def test_generate_whitelist_cookies(self):
        parser = flat_file.FlatFile('./tests/data/cookies.txt')
        self.assertEqual(cookies.generate_whitelist(parser, []), [{'wl': [42000227], 'mz':['$HEADERS_VAR:cookie'], 'msg': 'Cookies'}])
        self.assertEqual(cookies.generate_whitelist(parser, [{'wl': [42000227]}]), [])

    def test_generate_whitelist_images(self):
        parser = flat_file.FlatFile('./tests/data/images_1002.txt')
        self.assertEqual(
            images_1002.generate_whitelist(parser, []),
            [{'mz': ['$URL_X:^/phpMyAdmin-2.8.2/scripts/setup.php|URL'], 'wl': [1002], 'msg': 'Images size (0x)'}]
        )

        self.assertEqual(images_1002.generate_whitelist(parser, [{'wl': [1002]}]), [])
        