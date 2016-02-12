import json
import pathlib
import shutil
import tempfile
import unittest

from freenom_dns_updater import Config, Domain, Record, RecordType
import httpretty
import ipaddress


class ConfigTest(unittest.TestCase):

    def setUp(self):
        self.original_config_file = pathlib.Path(__file__).parent / "resources" / 'freenom.yml'
        self.config_file = pathlib.Path(__file__).parent / "resources" / 'test_freenom.yml'
        shutil.copy(str(self.original_config_file), str(self.config_file))
        self.config = Config(str(self.config_file))

    def tearDown(self):
        self.config_file.unlink()

    def test_reload(self):
        self.config.reload(str(self.config_file))
        self.test_get()

    def test_get(self):
        self.assertEqual('yourlogin@somemail.domain', self.config['login'])

    def test_set(self):
        self.config['login'] = 'test1'
        self.assertEqual('test1', self.config['login'])

    def test_login_get(self):
        self.assertEqual('yourlogin@somemail.domain', self.config.login)

    def test_password_get(self):
        self.assertEqual('yourpassword', self.config.password)

    def test_save(self):
        self.test_set()
        self.config.save()
        config = Config(str(self.config_file))
        self.assertEqual(self.config, config)

    @httpretty.activate
    def test_get_records(self):
        httpretty.register_uri(httpretty.GET, 'http://v6.ipv6-test.com/api/myip.php?json',
                               body=json.dumps({
                                   "address": "fd2b:1c1b:3641:1cd8::",
                                   "proto": "ipv6"}),
                               content_type='text/json')
        httpretty.register_uri(httpretty.GET, 'http://v4.ipv6-test.com/api/myip.php?json',
                               body=json.dumps({
                                   "address": "49.20.57.31",
                                   "proto": "ipv4"}),
                               content_type='text/json')

        records = self.config.records
        self.assertEqual(8, len(records))

        domain_1 = Domain("test.tk")
        record_1 = Record(
            target=str(ipaddress.ip_address("49.20.57.31")),
            type=RecordType.A,
            domain=domain_1
        )

        record_2 = Record(
            target=str(ipaddress.ip_address("49.20.57.31")),
            type=RecordType.A,
            name='mysubdomain',
            domain=domain_1
        )

        record_3 = Record(
            target=str(ipaddress.ip_address("fd2b:1c1b:3641:1cd8::")),
            type=RecordType.AAAA,
            name='mysubdomain',
            domain=domain_1
        )

        record_4 = Record(
            target=str(ipaddress.ip_address("fd2b:1c1b:3641:1cd8::")),
            type=RecordType.AAAA,
            domain=domain_1
        )

        domain_2 = Domain("test2.tk")
        record_5 = Record(
            target=str(ipaddress.ip_address("fd2b:1c1b:3641:1cd8::")),
            type=RecordType.AAAA,
            domain=domain_2,
            ttl=24440
        )

        record_6 = Record(
            name='mysubdomain',
            target=str(ipaddress.ip_address("49.20.57.31")),
            type=RecordType.A,
            domain=domain_2,
        )

        record_7 = Record(
            name='ipv6sub',
            target=str(ipaddress.ip_address("fd2b:1c1b:3641:1cd8::")),
            type=RecordType.AAAA,
            domain=domain_2,
        )

        record_8 = Record(
            name='ipv4sub',
            target=str(ipaddress.ip_address("64.64.64.64")),
            type=RecordType.A,
            domain=domain_2,
        )

        self.assertIn(record_1, records)
        self.assertIn(record_2, records)
        self.assertIn(record_3, records)
        self.assertIn(record_3, records)
        self.assertIn(record_4, records)
        self.assertIn(record_5, records)
        self.assertIn(record_6, records)
        self.assertIn(record_7, records)
        self.assertIn(record_8, records)

if __name__ == '__main__':
    unittest.main()
