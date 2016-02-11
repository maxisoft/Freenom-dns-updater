import datetime
import pathlib
import unittest

from freenom_dns_updater import Domain
from freenom_dns_updater.domain_parser import DomainParser


class DomainParserTest(unittest.TestCase):
    def test_parse_domains(self):
        path = pathlib.Path(__file__).parent / "resources" / "domain_page.html"
        with path.open() as f:
            html = f.read()
        domains = DomainParser.parse(html)
        self.assertEqual(2, len(domains))
        expected = Domain()
        expected.id = "1065251102"
        expected.name = "domain.tk"
        expected.register_date = datetime.date(year=2016, month=2, day=9)
        expected.expire_date = datetime.date(year=2017, month=2, day=9)
        expected.state = "Active"
        expected.type = "Free"
        self.assertIn(expected, domains)


if __name__ == '__main__':
    unittest.main()
