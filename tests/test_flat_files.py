import unittest

from nxtool.log_providers import flat_file
from nxtool.whitelists_generators import cookies, images_1002, zone_wide, zone_var_wide, url_wide, site_wide_id
from nxtool.whitelists_generators import google_analytics, zone_var_wide_url, array_like_variables_names


class TestFlatFiles(unittest.TestCase):
    def test_get_relevant_ids(self):
        parser = flat_file.FlatFile('./tests/data/cookies.txt')
        self.assertEquals(parser.get_relevant_ids(['zone', ], 1, 1), [42000227])
        self.assertEquals(parser.get_relevant_ids(['zone', ], 1, 100), [])


class TestParseLog(unittest.TestCase):
    maxDiff = None
    def test_show_stats(self):
        parser = flat_file.FlatFile('tests/data/logs.txt')
        parser.get_statistics()

    def test_generate_whitelist_cookies(self):
        parser = flat_file.FlatFile('./tests/data/cookies.txt')
        parser.get_relevant_ids = lambda x: [42000227]
        self.assertEqual(cookies.generate_whitelist(parser, []), [{'wl': [42000227], 'mz':['$HEADERS_VAR:cookie'],
                                                                   'msg': 'Cookies that matches a id 42000227'}])

        self.assertEqual(cookies.generate_whitelist(parser, [{'id':1234}]), [{'wl': [42000227], 'mz':['$HEADERS_VAR:cookie'],
                                                                   'msg': 'Cookies that matches a id 42000227'}])
    def test_generate_whitelist_images(self):
        parser = flat_file.FlatFile('./tests/data/images_1002.txt')
        self.assertEqual(
            images_1002.generate_whitelist(parser, []),
            [{'mz': ['$URL_X:^/phpMyAdmin-2.8.2/scripts/setup.php|URL'], 'wl': [1002], 'msg': 'Images size (0x)'}]
        )
        self.assertEqual(images_1002.generate_whitelist(parser, [{'wl': [1002]}]), [])

    def test_generate_whitelist_zone_wide(self):
        parser = flat_file.FlatFile('./tests/data/images_1002.txt')
        parser.get_top = lambda x: {1337: 2048, '': 1337} if x =='id' else {'ARGS': 2048}
        parser.get_relevant_ids = lambda x: [1337]
        self.assertEqual(zone_wide.generate_whitelist(parser, []),
                         [{'msg': 'zone-wide ID whitelist if it matches a id 1337', 'mz': ['ARGS'], 'wl': {1337}}])

        parser.get_relevant_ids = lambda x: []
        self.assertEqual(zone_wide.generate_whitelist(parser, [{'id':1337}]), [])

        parser.get_top = lambda x: {1337: 2} if x =='id' else {'ARGS': 2}
        self.assertEqual(zone_wide.generate_whitelist(parser, []), [])

    def test_generate_whitelist_zone_var_wide(self):
        parser = flat_file.FlatFile('./tests/data/images_1002.txt')
        parser.get_relevant_ids = lambda x: [1337]
        parser.get_top = lambda x: {'test_var_name': 2048, '':123, 'super-test':12}
        expected = [
            {'msg': 'Variable zone-wide if it matches a id 1337', 'mz': ['BODY:test_var_name'], 'wl': [1337]},
            {'msg': 'Variable zone-wide if it matches a id 1337', 'mz': ['ARGS:test_var_name|NAME'], 'wl': [1337]},
            {'msg': 'Variable zone-wide if it matches a id 1337', 'mz': ['ARGS:test_var_name'], 'wl': [1337]},
            {'msg': 'Variable zone-wide if it matches a id 1337', 'mz': ['BODY:test_var_name|NAME'], 'wl': [1337]}
        ]
        try:
            self.assertCountEqual(zone_var_wide.generate_whitelist(parser, []), expected)
        except AttributeError:  # Python2/3 fuckery
            self.assertItemsEqual(zone_var_wide.generate_whitelist(parser, []), expected)

        parser.get_top = lambda x: {'test_var_name': 0}
        try:
            self.assertCountEqual(zone_var_wide.generate_whitelist(parser, [{'id':1, 'mz':'BODY'}]), [])
        except AttributeError:  # Python2/3 fuckery
            self.assertItemsEqual(zone_var_wide.generate_whitelist(parser, [{'id':1, 'mz':'BODY'}]), [])


    def test_generate_whitelist_url_wide(self):
        parser = flat_file.FlatFile('./tests/data/images_1002.txt')
        parser.get_relevant_ids = lambda x: [1337]
        parser.get_top = lambda x: {'1337': 2048, '123': 2}
        expected = [{'msg': 'url-wide whitelist if it matches a id 1337', 'mz': ['$URL:1337'], 'wl': {'1337'}},
                          {'msg': 'url-wide whitelist if it matches a id 1337', 'mz': ['$URL:123'], 'wl': {'1337'}}]
        self.assertTrue(all(i in url_wide.generate_whitelist(parser, []) for i in expected))

        parser.get_relevant_ids = lambda x: []
        parser.get_top = lambda x: {}
        self.assertEqual(url_wide.generate_whitelist(parser, [{'id': 1337}]), [])

    def test_generate_whitelist_site_wide_id(self):
        parser = flat_file.FlatFile('./tests/data/images_1002.txt')
        parser.get_relevant_ids = lambda x, y: [1337]
        parser.get_top = lambda x: {'1337': 2048}
        self.assertEqual(site_wide_id.generate_whitelist(parser, []),
                         [{'msg': 'Site-wide id+zone if it matches id 1337', 'mz': ['1337'], 'wl': [1337]}])
        self.assertEqual(site_wide_id.generate_whitelist(parser, [{'id':1234}]),
                         [{'msg': 'Site-wide id+zone if it matches id 1337', 'mz': ['1337'], 'wl': [1337]}])

    def test_generate_whitelist_google_analytics(self):
        parser = flat_file.FlatFile('./tests/data/images_1002.txt')
        parser.get_relevant_ids = lambda x: [1337]
        parser.get_top = lambda x: {'1337': 2048}
        self.assertEqual(google_analytics.generate_whitelist(parser, []),
                         [{'msg': 'Google analytics', 'mz': ['$ARGS_VAR_X:__utm[abctvz]'], 'wl': [1337]}])
        self.assertEqual(google_analytics.generate_whitelist(parser, [{'id':1234}]),
                         [{'msg': 'Google analytics', 'mz': ['$ARGS_VAR_X:__utm[abctvz]'], 'wl': [1337]}])
        self.assertEqual(google_analytics.generate_whitelist(parser, [{'wl':1002}]),
                         [{'msg': 'Google analytics', 'mz': ['$ARGS_VAR_X:__utm[abctvz]'], 'wl': [1337]}])

    def test_generate_whitelist_zone_var_wide_url(self):
        parser = flat_file.FlatFile('./tests/data/images_1002.txt')
        parser.get_relevant_ids = lambda x: [1337]
        parser.get_top = lambda x: {'1337': 2048, '': 123, 'test': 1}
        expected = [
            {
                'msg': 'Variable zone-wide on a specific url if it matches a id 1337',
                'mz': ['$URL:1337|$BODY_VAR:1337'],
                'wl': [1337]
            },
            {
                'msg': 'Variable zone-wide on a specific url if it matches a id 1337',
                'mz': ['$URL:1337|ARGS:1337|NAME'],
                'wl': [1337]
            },
            {'msg': 'Variable zone-wide on a specific url if it matches a id 1337',
             'mz': ['$URL:1337|$ARGS_VAR:1337'],
             'wl': [1337]
             },
            {
                'msg': 'Variable zone-wide on a specific url if it matches a id 1337',
                'mz': ['$URL:1337|BODY:1337|NAME'],
                'wl': [1337]
            }]
        self.assertTrue(all(i in zone_var_wide_url.generate_whitelist(parser, [{'id':123}]) for i in expected))

    def test_generate_whitelist_array_like_variables_names(self):
        parser = flat_file.FlatFile('./tests/data/images_1002.txt')
        parser.get_relevant_ids = lambda x: [1337]
        parser.get_top = lambda x: {'1337': 2048}
        self.assertEqual(array_like_variables_names.generate_whitelist(parser, []), [])

        parser.get_relevant_ids = lambda x: [1310]
        parser.get_top = lambda x: {'test[1234]': 2048}
        self.assertEqual(array_like_variables_names.generate_whitelist(parser, []), [
            {'msg': 'Array-like variable name', 'mz': ['$BODY_VAR_X:^test\\[.+\\]$'], 'wl': [1310, 1311]},
            {'msg': 'Array-like variable name', 'mz': ['$ARGS_VAR_X:^test\\[.+\\]$'],'wl': [1310, 1311]}]
                                                                       )
        self.assertEqual(array_like_variables_names.generate_whitelist(parser, [{'id':3, 'mz':'BODY'}]), [
            {'msg': 'Array-like variable name', 'mz': ['$BODY_VAR_X:^test\\[.+\\]$'], 'wl': [1310, 1311]},
            {'msg': 'Array-like variable name', 'mz': ['$ARGS_VAR_X:^test\\[.+\\]$'],'wl': [1310, 1311]}]
                                                                       )
        parser.get_top = lambda x: {'test[1234]]': 2048}
        self.assertEqual(array_like_variables_names.generate_whitelist(parser, []), [])

        parser.get_top = lambda x: {'test[[1234]': 2048}
        self.assertEqual(array_like_variables_names.generate_whitelist(parser, []), [])

        parser.get_top = lambda x: {'test[1234]': 1}
        self.assertEqual(array_like_variables_names.generate_whitelist(parser, []), [])

class TestFiltering(unittest.TestCase):
    def test_filter_str(self):
        parser = flat_file.FlatFile('./tests/data/cookies.txt')
        self.assertEquals([i for i in parser.get_results()][0], {'block': '0',
           'cscore0': '$UWA', 'id0': '42000227', 'ip': 'X.X.X.X', 'learning': '0', 'score0': '8',
           'server': 'Y.Y.Y.Y', 'total_blocked': '204', 'total_processed': '472',
           'uri': '/phpMyAdmin-2.8.2/scripts/setup.php', 'var_name0': 'cookie', 'vers': '0.52', 'zone0': 'HEADERS'}
        )

    def test_filter_list(self):
        parser = flat_file.FlatFile('./tests/data/cookies.txt')
        parser.add_filters({'ip': ['X.X.X.X', 'A.A.A.A']})
        self.assertEquals([i for i in parser.get_results()], [{'block': '0',
           'cscore0': '$UWA', 'id0': '42000227', 'ip': 'X.X.X.X', 'learning': '0', 'score0': '8',
           'server': 'Y.Y.Y.Y', 'total_blocked': '204', 'total_processed': '472',
           'uri': '/phpMyAdmin-2.8.2/scripts/setup.php', 'var_name0': 'cookie', 'vers': '0.52', 'zone0': 'HEADERS'}])

        parser = flat_file.FlatFile('./tests/data/cookies.txt')
        parser.add_filters({'ip': ['A.A.A.A']})
        self.assertEquals([i for i in parser.get_results()], [])

        parser = flat_file.FlatFile('./tests/data/cookies.txt')
        parser.add_filters({'ip': ['X.X.X.X']}, negative=True)
        self.assertEquals([i for i in parser.get_results()], [])