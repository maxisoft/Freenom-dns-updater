import requests
import ipaddress

__all__ = ['get_my_ip', 'get_my_ipv4', 'get_my_ipv6']


def get_my_ip(url='http://v4v6.ipv6-test.com/api/myip.php?json', timeout=30):
    with requests.get(url, timeout=timeout) as r:
        r.raise_for_status()
        return ipaddress.ip_address(r.json()['address'])


def get_my_ipv4(url='http://v4.ipv6-test.com/api/myip.php?json', timeout=30):
    with requests.get(url, timeout=timeout) as r:
        r.raise_for_status()
        return ipaddress.IPv4Address(r.json()['address'])


def get_my_ipv6(url='http://v6.ipv6-test.com/api/myip.php?json', timeout=30):
    with requests.get(url, timeout=timeout) as r:
        r.raise_for_status()
        return ipaddress.IPv6Address(r.json()['address'])