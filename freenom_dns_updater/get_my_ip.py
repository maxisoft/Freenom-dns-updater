import requests
import ipaddress

__all__ = ['get_my_ip', 'get_my_ipv4', 'get_my_ipv6']

def get_my_ip(url='http://v4v6.ipv6-test.com/api/myip.php?json', timeout=30):
    return ipaddress.ip_address(requests.get(url, timeout=timeout).json()['address'])


def get_my_ipv4(url='http://v4.ipv6-test.com/api/myip.php?json', timeout=30):
    return ipaddress.IPv4Address(requests.get(url, timeout=timeout).json()['address'])


def get_my_ipv6(url='http://v6.ipv6-test.com/api/myip.php?json', timeout=30):
    return ipaddress.IPv6Address(requests.get(url, timeout=timeout).json()['address'])