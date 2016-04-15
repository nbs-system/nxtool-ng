import unittest
import datetime

from nxapi import log_parsers


class TestParseLog(unittest.TestCase):
    def test_parse_correct_log(self):
        parsed = log_parsers.parse_log('2013/11/10 07:36:19 [error] 8278#0: *5932 NAXSI_FMT: ip=X.X.X.X&server=Y.Y.Y.Y&uri=/phpMyAdmin-2.8.2/scripts/setup.php&learning=0&vers=0.52&total_processed=472&total_blocked=204&block=0&cscore0=$UWA&score0=8&zone0=HEADERS&id0=42000227&var_name0=user-agent, client: X.X.X.X, server: blog.memze.ro, request: "GET /phpMyAdmin-2.8.2/scripts/setup.php HTTP/1.1", host: "X.X.X.X"')
        self.assertEqual(parsed[0], datetime.datetime(2013, 11, 10, 7, 36, 19))
        self.assertEqual(parsed[1]['total_processed'], '472')
        self.assertEqual(parsed[1]['vers'], '0.52')
        self.assertEqual(parsed[1]['learning'], '0')
        self.assertEqual(parsed[1]['cscore0'], '$UWA')
        self.assertEqual(parsed[1]['var_name0'], 'user-agent')
        self.assertEqual(parsed[1]['ip'], 'X.X.X.X')
        self.assertEqual(parsed[1]['uri'], '/phpMyAdmin-2.8.2/scripts/setup.php')
        self.assertEqual(parsed[1]['id0'], '42000227')
        self.assertEqual(parsed[1]['server'], 'Y.Y.Y.Y')
        self.assertEqual(parsed[1]['zone0'], 'HEADERS')
        self.assertEqual(parsed[1]['score0'], '8')
        self.assertEqual(parsed[1]['total_blocked'], '204')
        self.assertEqual(parsed[1]['block'], '0')

    def test_parse_invalid_log(self):
        parsed = log_parsers.parse_log('2013/11/10 07:36:19 lol')
        self.assertEqual(parsed, None)

        parsed = log_parsers.parse_log('2013/11/10 07:36:19 [error] 8278#0: *5932 NAXSI_FMMT: ip=X.X.X.X&server=Y.Y.Y.Y&uri=/phpMyAdmin-2.8.2/scripts/setup.php&learning=0&vers=0.52&total_processed=472&total_blocked=204&block=0&cscore0=$UWA&score0=8&zone0=HEADERS&id0=42000227&var_name0=user-agent, client: X.X.X.X, server: blog.memze.ro, request: "GET /phpMyAdmin-2.8.2/scripts/setup.php HTTP/1.1", host: "X.X.X.X"')
        self.assertEqual(parsed, None)

        parsed = log_parsers.parse_log('2013/11/10 07:36:19 [error] 8278#0: *5932 NAXSI_FMT: ip=X.X.X.X&server=Y.Y.Y.Y&uri=/phpMyAdmin-2.8.2/scripts/setup.php&learning=0&vers=0.52&total_processed=472&total_blocked=204&block=0&cscore0=$UWA&score0=8&zone0=HEADERS&id0=42000227&id1=123&var_name0=user-agent, client: X.X.X.X, server: blog.memze.ro, request: "GET /phpMyAdmin-2.8.2/scripts/setup.php HTTP/1.1", host: "X.X.X.X"')
        self.assertEqual(parsed, None)