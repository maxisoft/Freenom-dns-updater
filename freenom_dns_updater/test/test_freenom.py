import pathlib
import unittest
from pprint import pprint

import datetime
import requests
import os
import six

from freenom_dns_updater import Freenom, Config, Domain


class FreenomTest(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(FreenomTest, self).__init__(*args, **kwargs)
        self.config_file = self.find_freenom_config_file()

    def setUp(self):
        self.freenom = Freenom()
        if self.config_file:
            self.config = Config(str(self.config_file))
            self.login = os.getenv("FREENOM_LOGIN", self.config.login)
            self.password = os.getenv("FREENOM_PASSWORD", self.config.password)
        else:
            self.config = None
            self.login = os.getenv("FREENOM_LOGIN", "default")
            self.password = os.getenv("FREENOM_PASSWORD", "default")

    @staticmethod
    def find_freenom_config_file():
        current_path = pathlib.Path().absolute()
        p = current_path
        for i in range(3):
            target = p / "freenom.yml"
            if target.exists():
                return target
            p = p.parent
        return None

    def test_init(self):
        self.assertIsInstance(self.freenom.session, requests.Session)

    def test_login(self):
        self.assertTrue(self.freenom.login(self.login, self.password))

    def test_login_fail(self):
        self.assertFalse(self.freenom.login(self.login, ""))

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


if __name__ == '__main__':
    unittest.main()
