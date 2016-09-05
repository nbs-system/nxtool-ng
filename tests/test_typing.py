import unittest
from nxtool import typing
from nxtool.log_providers import flat_file

class TestTyping(unittest.TestCase):
    def test_typing(self):
        parser = flat_file.FlatFile('./tests/data/exlog.txt')
        self.assertEquals([i for i in typing.typification(parser)], [])