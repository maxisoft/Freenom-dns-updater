import pathlib
import random
import unittest
from pprint import pprint

import datetime
import requests
import os
import six

from freenom_dns_updater import Freenom, Config, Domain, Record, RecordType
from freenom_dns_updater.exception import UpdateError


'''
This test suite test the fdu unofficial api in real use case scenario.
To use this suite you need a freenom account with at least 1 domain registered (for testing).

Temporary export your login password as the following env variables: FREENOM_LOGIN and FREENOM_PASSWORD,
then write your testing domain id and name as env variables : FREENOM_TEST_DOMAIN_ID and FREENOM_TEST_DOMAIN_NAME
'''

TEST_DOMAIN_ID = int(os.getenv("FREENOM_TEST_DOMAIN_ID", 1027889227))
TEST_DOMAIN_NAME = str(os.getenv("FREENOM_TEST_DOMAIN_NAME", 'freenom-dns-updater.tk'))


class FreenomTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(FreenomTest, self).__init__(*args, **kwargs)
        self.config_file = self.find_config_file("freenom.yml")

    def setUp(self):
        self.freenom = Freenom()
        if self.config_file:
            self.config = Config(str(self.config_file))
            self.login = os.getenv("FREENOM_LOGIN", self.config.login)
            self.password = os.getenv("FREENOM_PASSWORD", self.config.password)
        else:
            self.config = None
            self.login = os.getenv("FREENOM_LOGIN", None)
            self.password = os.getenv("FREENOM_PASSWORD", None)

    @staticmethod
    def find_config_file(name):
        current_path = pathlib.Path().absolute()
        p = current_path
        for i in range(3):
            target = p / name
            if target.exists():
                return target
            p = p.parent
        return None

    def test_init(self):
        self.assertIsInstance(self.freenom.session, requests.Session)

    def test_login(self):
        self.skipIfNoLogin()
        self.assertTrue(self.freenom.login(self.login, self.password))

    def test_login_fail(self):
        self.assertFalse(self.freenom.login("", ""))

    def test__get_token(self):
        result = self.freenom._get_login_token()
        self.assertIsInstance(result, six.string_types)
        self.assertTrue(result)

    def test__get_token_no_token(self):
        six.assertRaisesRegex(self,
                              AssertionError,
                              "there's no token",
                              self.freenom._get_login_token, "http://httpbin.org/html")

    def test_is_logged_in(self):
        self.assertFalse(self.freenom.is_logged_in())
        self.test_login()
        self.assertTrue(self.freenom.is_logged_in())

    def test_manage_domain_url(self):
        domain = Domain()
        domain.id = '1012705422'
        domain.name = 'domain.cf'
        self.assertEqual(
            'https://my.freenom.com/clientarea.php?managedns=domain.cf&domainid=1012705422',
            self.freenom.manage_domain_url(domain)
        )

    def test_add_record(self):
        domain = Domain()
        domain.id = TEST_DOMAIN_ID
        domain.name = TEST_DOMAIN_NAME

        record = Record()
        record.domain = domain
        record.name = "TESTADD"
        record.type = RecordType.A
        record.target = "185.45.193.%d" % random.randint(5, 200)
        record.ttl = random.choice((14440, 14440 / 2, 14440 * 2))

        self.test_login()
        self.remove_record_if_exists(record)
        try:
            res = self.freenom.add_record(record)
            self.assertTrue(bool(res))
            records = self.freenom.list_records(domain)
            self.assertIn(record, records)
        finally:
            self.freenom.remove_record(record)

    def test_update_record(self):
        domain = Domain()
        domain.id = TEST_DOMAIN_ID
        domain.name = TEST_DOMAIN_NAME

        record = Record()
        record.domain = domain
        record.name = "TESTUPDATE"
        record.type = RecordType.A
        record.target = "185.45.193.%d" % random.randint(5, 200)
        record.ttl = 14440

        self.test_login()
        self.add_record_if_missing(record)
        record.ttl = 14440 * 2
        try:
            res = self.freenom.update_record(record)
            self.assertTrue(bool(res))
            self.assertIn(record, self.freenom.list_records(domain))
        finally:
            self.freenom.remove_record(record)

    def test_update_record_fail(self):
        domain = Domain()
        domain.id = TEST_DOMAIN_ID
        domain.name = TEST_DOMAIN_NAME

        record = Record()
        record.domain = domain
        record.name = "TESTUPDATEBUG"
        record.type = RecordType.A
        record.target = "185.45.193.%d" % random.randint(5, 200)
        record.ttl = 14440

        self.test_login()
        self.add_record_if_missing(record)
        records_before = self.freenom.list_records(domain)
        record.target = "185.45.193.%d" % random.randint(1000, 3500)
        try:
            self.freenom.update_record(record)
        except UpdateError as e:
            self.assertEqual(1, len(e.msgs))
            self.assertIn('Error occured: Invalid value in dnsrecord', e.msgs)
            self.assertEqual(record, e.record)
            self.assertListEqual(records_before, e.old_record_list)
        else:
            self.fail("exception %s expected " % UpdateError.__name__)
        finally:
            self.freenom.remove_record(record)

    def test_remove_record(self):
        domain = Domain()
        domain.id = TEST_DOMAIN_ID
        domain.name = TEST_DOMAIN_NAME

        record = Record()
        record.domain = domain
        record.name = "TESTREMOVE"
        record.type = RecordType.A
        record.target = "185.45.193.%d" % random.randint(5, 200)
        record.ttl = 14440

        self.test_login()
        self.add_record_if_missing(record)

        res = self.freenom.remove_record(record)
        self.assertTrue(res)
        self.assertNotIn(record, self.freenom.list_records(domain))

    def add_record_if_missing(self, record):
        if record not in self.freenom:
            self.freenom.add_record(record)

    def remove_record_if_exists(self, record):
        if record in self.freenom:
            self.freenom.remove_record(record)

    def skipIfNoLogin(self):
        if self.login is None and self.password is None:
            self.skipTest("login and password are not set")


if __name__ == '__main__':
    unittest.main()
