import unittest

import requests
from freenom_dns_updater.freenom import Freenom
import secret


class FreenomTest(unittest.TestCase):

    def setUp(self):
        self.freenom = Freenom()

    def test_init(self):
        self.assertIsInstance(self.freenom.session, requests.Session)

    def test_login(self):
        self.assertTrue(self.freenom.login(secret.login, secret.password))

    def test_login_fail(self):
        self.assertFalse(self.freenom.login(secret.login, ""))

    def test__get_login_token(self):
        result = self.freenom._get_login_token()
        self.assertIsInstance(result, str)
        self.assertTrue(result)

    def test_is_logged_in(self):
        self.assertFalse(self.freenom.is_logged_in())
        self.test_login()
        self.assertTrue(self.freenom.is_logged_in())

    def test__get_login_token_no_token(self):
        self.assertRaisesRegex(AssertionError,
                               "there's no token",
                               self.freenom._get_login_token, "http://httpbin.org/html")


if __name__ == '__main__':
    unittest.main()
