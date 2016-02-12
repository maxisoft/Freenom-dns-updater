import unittest
import ipaddress

import requests.exceptions

from freenom_dns_updater.get_my_ip import *


class GetMyIpTest(unittest.TestCase):

    def test_get_my_ip(self):
        res = get_my_ip()
        self.assertIsInstance(res, ipaddress._BaseAddress)

    def test_get_my_ipv4(self):
        res = get_my_ipv4()
        self.assertIsInstance(res, ipaddress.IPv4Address)

    def test_get_my_ipv6(self):
        res = get_my_ipv6()
        self.assertIsInstance(res, ipaddress.IPv6Address)

    def test_get_my_ip_timeout(self):
        self.assertRaises(requests.exceptions.Timeout, get_my_ip, "https://httpbin.org/delay/10", **{'timeout': 2})


if __name__ == '__main__':
    unittest.main()
