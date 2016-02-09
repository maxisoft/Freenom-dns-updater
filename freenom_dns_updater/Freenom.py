import requests
from bs4 import BeautifulSoup

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

    def is_logged_in(self, r=None, url="https://my.freenom.com/clientarea.php"):
        if r is None:
            r = self.session.get(url)
            assert r, "could't get %s" % url
        return '<li class="addFunds">' in r.text

    def _get_login_token(self, url="https://my.freenom.com/clientarea.php"):
        r = self.session.get(url)
        assert r, "could't get %s" % url
        soup = BeautifulSoup(r.text, "html.parser")
        token = soup.find("input", {'name': 'token'})
        assert token and token['value'], "there's no token on this page"
        return token['value']



