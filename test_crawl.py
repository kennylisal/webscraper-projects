import unittest
from crawl import normalize_url

class TestCrawl(unittest.TestCase):
    def test_normalize_url(self):
        input_url = 'http://Example.com/path/?b=2&a=1#section'
        actual = normalize_url(input_url)
        expected = "example.com/path?b=2&a=1"
        self.assertEqual(actual,expected)

if __name__ == "__main__":
    unittest.main()