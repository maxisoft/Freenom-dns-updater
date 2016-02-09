import re

import requests
from bs4 import BeautifulSoup, Tag
from .domain import Domain

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
        assert r, "could't get %s" % url
        return self.is_logged_in(r)

    def list_domain(self, url='https://my.freenom.com/clientarea.php?action=domains'):
        token = self._get_domain_token()
        playload = {'token': token,
                    'itemlimit': 'all'}
        r = self.session.post(url, playload)
        assert r, "could't get %s" % url
        self.parse_domains(r.text)

    def parse_domains(self, raw_html):
        soup = BeautifulSoup(raw_html, "html.parser")
        tag = soup.find("form", {'id': 'bulkactionform'})
        assert isinstance(tag, Tag)
        raw_domains = tag.select("tbody > tr")
        ret = []
        for raw_domain in raw_domains:
            assert isinstance(raw_domain, Tag)
            props = raw_domain.find_all("td")
            domain = Domain()
            domain.name = props[0].text.strip()
            domain.register_date = props[1].text
            domain.expire_date = props[2].text
            domain.state = props[3].text
            domain.type = props[4].text
            domain.id = props[5].find('a')['href']
            domain.id = re.match("clientarea\.php\?action=domaindetails&id=(\d+)", domain.id).group(1)
            ret.append(domain)
        return ret

    def is_logged_in(self, r=None, url="https://my.freenom.com/clientarea.php"):
        if r is None:
            r = self.session.get(url)
            assert r, "could't get %s" % url
        return '<li class="addFunds">' in r.text

    def _get_login_token(self, url="https://my.freenom.com/clientarea.php"):
        return self._get_token(url)

    def _get_domain_token(self, url='https://my.freenom.com/clientarea.php?action=domains'):
        return self._get_token(url)

    def _get_token(self, url):
        r = self.session.get(url)
        assert r, "could't get %s" % url
        soup = BeautifulSoup(r.text, "html.parser")
        token = soup.find("input", {'name': 'token'})
        assert token and token['value'], "there's no token on this page"
        return token['value']
