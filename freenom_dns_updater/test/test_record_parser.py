import datetime
import pathlib
import unittest

from freenom_dns_updater import Record, RecordType
from freenom_dns_updater.record_parser import RecordParser


class DomainParserTest(unittest.TestCase):
    def test_parse_records(self):
        path = pathlib.Path(__file__).parent / "resources" / "record_page.html"
        with path.open() as f:
            html = f.read()
        records = RecordParser.parse(html)
        self.assertEqual(2, len(records))
        expected = Record()
        expected.target = "2a04:dd00::327b:8888"
        expected.ttl = 800
        expected.name = "IPV6"
        expected.type = RecordType.AAAA
        self.assertIn(expected, records)


if __name__ == '__main__':
    unittest.main()
