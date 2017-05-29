import re

import pathlib
import requests
from bs4 import BeautifulSoup, Tag
from copy import copy

from .record import Record
from .domain import Domain
from .exception import UpdateError, AddError, DnsRecordBaseException
from .domain_parser import DomainParser
from .record_parser import RecordParser


default_user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"


class Freenom(object):
    def __init__(self, user_agent=default_user_agent, *args, **kwargs):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})
        self.session.verify = self.findcert() or False

    @staticmethod
    def findcert():
        p = pathlib.Path(__file__).parent
        p = (p / "data" / "chain.pem")
        if p.exists():
            return str(p)
        return None

    def login(self, login, password, url="https://my.freenom.com/dologin.php"):
        token = self._get_login_token()
        playload = {'token': token,
                    'username': login,
                    'password': password}
        r = self.session.post(url, playload)
        assert r, "couldn't get %s" % url
        return self.is_logged_in(r)

    def list_domains(self, url='https://my.freenom.com/clientarea.php?action=domains'):
        token = self._get_domain_token()
        playload = {'token': token,
                    'itemlimit': 'all'}
        r = self.session.post(url, playload)
        assert r, "couldn't get %s" % url
        return DomainParser.parse(r.text)

    def list_records(self, domain):
        url = self.manage_domain_url(domain)
        r = self.session.get(url)
        assert r, "couldn't get %s" % url
        ret = RecordParser.parse(r.text)
        for records in ret:
            records.domain = domain
        return ret

    def add_record(self, record, upsert=True, records=None):
        if records is None:
            records = self.list_records(record.domain)
        contains_record = self.contains_record(record, records)
        if contains_record:
            if upsert:
                return self.update_record(record, records=records)
            else:
                return False

        url = self.manage_domain_url(record.domain)
        token = self._get_manage_domain_token(url)
        playload = {
            'dnsaction': 'add',
            'token': token
        }
        record_id = "addrecord[%d]" % 0
        playload[record_id + "[name]"] = str(record.name)
        playload[record_id + "[type]"] = record.type.name
        playload[record_id + "[ttl]"] = str(record.ttl)
        playload[record_id + "[value]"] = str(record.target)
        playload[record_id + "[priority]"] = ""
        playload[record_id + "[port]"] = ""
        playload[record_id + "[weight]"] = ""
        playload[record_id + "[forward_type]"] = "1"

        r = self.session.post(url, data=playload)
        soup = BeautifulSoup(r.text, "html.parser")
        errs = soup.find_all(attrs={'class': 'dnserror'})
        if errs:
            raise AddError([e.text for e in errs], record, records)
        return len(soup.find_all(attrs={'class': 'dnssuccess'}))

    def update_record(self, record, records=None):
        url = self.manage_domain_url(record.domain)
        token = self._get_manage_domain_token(url)
        playload = {
            'dnsaction': 'modify',
            'token': token
        }

        if records is None:
            records = self.list_records(record.domain)
        for i, rec in enumerate(records):
            record_id = "records[%d]" % i
            if rec.name == record.name and rec.type == record.type:
                rec = record
            playload[record_id + "[line]"] = ""
            playload[record_id + "[type]"] = rec.type.name
            playload[record_id + "[name]"] = str(rec.name)
            playload[record_id + "[ttl]"] = str(rec.ttl)
            playload[record_id + "[value]"] = str(rec.target)

        r = self.session.post(url, data=playload)
        soup = BeautifulSoup(r.text, "html.parser")
        errs = soup.find_all(attrs={'class': 'dnserror'})
        if errs:
            raise UpdateError([e.text for e in errs], record, records)
        return len(soup.find_all(attrs={'class': 'dnssuccess'}))

    def remove_record(self, record, records=None):
        if records is None:
            records = self.list_records(record.domain)
        if not self.contains_record(record, records):
            return False
        record = copy(record)
        record.target = "-@^^ ac1a3!"  # somehow hacky, isn't ?
        try:
            self.update_record(record, records)
        except UpdateError as e:
            return len(e.msgs) == 1
        return False

    def contains_domain(self, domain, domains=None):
        if domains is None:
            domains = self.list_domains()
        return any(domain.id == d.id and domain.name == d.name for d in domains)

    def contains_record(self, record, records=None):
        if records is None:
            records = self.list_records(record.domain)
        return any(record.name == rec.name and record.type == rec.type for rec in records)

    def __contains__(self, item):
        if isinstance(item, Domain):
            return self.contains_domain(item)
        if isinstance(item, Record):
            return self.contains_record(item)
        return False

    def rollback_update(self, records):
        if not records:
            return False
        url = self.manage_domain_url(records[0].domain)
        token = self._get_manage_domain_token(url)
        playload = {
            'dnsaction': 'modify',
            'token': token
        }
        for i, rec in enumerate(records):
            record_id = "records[%d]" % i
            playload[record_id + "[line]"] = ""
            playload[record_id + "[type]"] = rec.type.name
            playload[record_id + "[name]"] = str(rec.name)
            playload[record_id + "[ttl]"] = str(rec.ttl)
            playload[record_id + "[value]"] = str(rec.target)

        return bool(self.session.post(url, data=playload))

    @staticmethod
    def manage_domain_url(domain):
        return "https://my.freenom.com/clientarea.php?managedns={0.name}&domainid={0.id}".format(domain)

    def is_logged_in(self, r=None, url="https://my.freenom.com/clientarea.php"):
        if r is None:
            r = self.session.get(url)
            assert r, "couldn't get %s" % url
        return '<section class="greeting">' in r.text

    def _get_login_token(self, url="https://my.freenom.com/clientarea.php"):
        return self._get_token(url)

    def _get_domain_token(self, url='https://my.freenom.com/clientarea.php?action=domains'):
        return self._get_token(url)

    def _get_manage_domain_token(self, url):
        return self._get_token(url)

    def _get_token(self, url):
        r = self.session.get(url)
        assert r, "couldn't get %s" % url
        soup = BeautifulSoup(r.text, "html.parser")
        token = soup.find("input", {'name': 'token'})
        assert token and token['value'], "there's no token on this page"
        return token['value']
