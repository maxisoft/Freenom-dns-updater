import unittest
import ipaddress

import httpretty
import json
import requests.exceptions
import six

from freenom_dns_updater.get_my_ip import *


class GetMyIpTestMock(unittest.TestCase):
    @httpretty.activate
    def test_get_my_ip(self):
        httpretty.register_uri(httpretty.GET, "http://test.com/",
                               body=json.dumps({
                                   "address": "fd2b:1c1b:3641:1cd8::",
                                   "proto": "ipv6"}),
                               content_type='text/json')

        res = get_my_ip('http://test.com/')
        self.assertIsInstance(res, ipaddress._BaseAddress)
        self.assertEqual(ipaddress.ip_address(u"fd2b:1c1b:3641:1cd8::"), res)

        httpretty.register_uri(httpretty.GET, "http://test.com/",
                               body=json.dumps({
                                   "address": "49.20.57.31",
                                   "proto": "ipv4"}),
                               content_type='text/json')

        res = get_my_ip('http://test.com/')
        self.assertIsInstance(res, ipaddress._BaseAddress)
        self.assertEqual(ipaddress.ip_address(u"49.20.57.31"), res)

    @httpretty.activate
    def test_get_my_ipv4(self):
        httpretty.register_uri(httpretty.GET, "http://test.com/",
                               body=json.dumps({
                                   "address": "49.20.57.31",
                                   "proto": "ipv4"}),
                               content_type='text/json')

        res = get_my_ipv4('http://test.com/')
        self.assertIsInstance(res, ipaddress.IPv4Address)
        self.assertEqual(ipaddress.ip_address(u"49.20.57.31"), res)

    @httpretty.activate
    def test_get_my_ipv6(self):
        httpretty.register_uri(httpretty.GET, "http://test.com/",
                               body=json.dumps({
                                   "address": "fd2b:1c1b:3641:1cd8::",
                                   "proto": "ipv6"}),
                               content_type='text/json')

        res = get_my_ipv6('http://test.com/')
        self.assertIsInstance(res, ipaddress.IPv6Address)
        self.assertEqual(ipaddress.ip_address(u"fd2b:1c1b:3641:1cd8::"), res)


class GetMyIpTestReal(unittest.TestCase):
    def test_get_my_ip(self):
        res = get_my_ip()
        self.assertIsInstance(res, ipaddress._BaseAddress)

    def test_get_my_ipv4(self):
        res = get_my_ipv4()
        self.assertIsInstance(res, ipaddress.IPv4Address)

    def test_get_my_ipv6(self):
        try:
            res = get_my_ipv6()
        except OSError:
            self.skipTest("localhost doesn't provide ipv6")
        except requests.exceptions.ConnectionError:
            self.skipTest("localhost doesn't provide ipv6")
        else:
            self.assertIsInstance(res, ipaddress.IPv6Address)

    def test_get_my_ip_timeout(self):
        self.assertRaises(requests.exceptions.Timeout, get_my_ip, "https://httpbin.org/delay/10", **{'timeout': 2})


if __name__ == '__main__':
    unittest.main()
