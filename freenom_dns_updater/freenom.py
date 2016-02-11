import re

import requests
from bs4 import BeautifulSoup, Tag

from .domain_parser import DomainParser
from .record_parser import RecordParser


default_user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"


class Freenom(object):
    def __init__(self, user_agent=default_user_agent, *args, **kwargs):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})

    def login(self, login, password, url="https://my.freenom.com/dologin.php"):
        token = self._get_login_token()
        playload = {'token': token,
                    'username': login,
                    'password': password}
        r = self.session.post(url, playload)
        assert r, "couldn't get %s" % url
        return self.is_logged_in(r)

    def list_domain(self, url='https://my.freenom.com/clientarea.php?action=domains'):
        token = self._get_domain_token()
        playload = {'token': token,
                    'itemlimit': 'all'}
        r = self.session.post(url, playload)
        assert r, "couldn't get %s" % url
        return DomainParser.parse(r.text)

    def list_record(self, domain):
        url = self.manage_domain_url(domain)
        r = self.session.get(url)
        assert r, "couldn't get %s" % url
        return RecordParser.parse(r.text)

    @staticmethod
    def manage_domain_url(domain):
        return "https://my.freenom.com/clientarea.php?managedns={0.name}&domainid={0.id}".format(domain)

    def is_logged_in(self, r=None, url="https://my.freenom.com/clientarea.php"):
        if r is None:
            r = self.session.get(url)
            assert r, "couldn't get %s" % url
        return '<li class="addFunds">' in r.text

    def _get_login_token(self, url="https://my.freenom.com/clientarea.php"):
        return self._get_token(url)

    def _get_domain_token(self, url='https://my.freenom.com/clientarea.php?action=domains'):
        return self._get_token(url)

    def _get_token(self, url):
        r = self.session.get(url)
        assert r, "couldn't get %s" % url
        soup = BeautifulSoup(r.text, "html.parser")
        token = soup.find("input", {'name': 'token'})
        assert token and token['value'], "there's no token on this page"
        return token['value']
