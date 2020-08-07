import pathlib
import warnings
from typing import Optional, List
from urllib.parse import urljoin, urlparse, quote

import requests
from bs4 import BeautifulSoup

from .domain import Domain
from .domain_parser import DomainParser
from .exception import UpdateError, AddError
from .record import Record
from .record_parser import RecordParser

default_user_agent = "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"

_base_url = "https://my.freenom.com"
parsed_base_url = urlparse(_base_url)
login_url = urljoin(_base_url, 'dologin.php')
client_area_url = urljoin(_base_url, 'clientarea.php')
list_domain_url = f'{client_area_url}?action=domains'


class Freenom(object):
    def __init__(self, user_agent: str = default_user_agent):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': user_agent})

    def __del__(self):
        self.session.close()

    @staticmethod
    def findcert():
        p = pathlib.Path(__file__).parent
        p = (p / "data" / "chain.pem")
        if p.exists():
            warnings.warn(f"Using custom chain.pem \"{p.absolute()}\"")
            return str(p)
        return None

    def login(self, login: str, password: str, url: str = login_url) -> bool:
        token = self._get_login_token()
        payload = {'token': token,
                   'username': login,
                   'password': password}
        host_name = urlparse(url).hostname
        if host_name != parsed_base_url.hostname:
            warnings.warn(f"Using another host than {parsed_base_url.hostname} is not tested")
        r = self.session.post(url, payload,
                              headers={'Host': host_name, 'Referer': f'https://{host_name}/clientarea.php'})
        r.raise_for_status()
        return self.is_logged_in(r)

    def list_domains(self, url: str = list_domain_url) -> List[Domain]:
        token = self._get_domain_token()
        payload = {'token': token,
                   'itemlimit': 'all'}
        r = self.session.post(url, payload)
        r.raise_for_status()
        return DomainParser.parse(r.text)

    def list_records(self, domain: Domain):
        url = self.manage_domain_url(domain)
        r = self.session.get(url)
        r.raise_for_status()
        ret = RecordParser.parse(r.text)
        for records in ret:
            records.domain = domain
        return ret

    def add_record(self, record: Record, upsert: bool = True, records: Optional[List[Record]] = None):
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
        payload = {
            'dnsaction': 'add',
            'token': token
        }
        record_id = "addrecord[%d]" % 0
        payload[record_id + "[name]"] = str(record.name)
        payload[record_id + "[type]"] = record.type.name
        payload[record_id + "[ttl]"] = str(record.ttl)
        payload[record_id + "[value]"] = str(record.target)
        payload[record_id + "[priority]"] = ""
        payload[record_id + "[port]"] = ""
        payload[record_id + "[weight]"] = ""
        payload[record_id + "[forward_type]"] = "1"

        r = self.session.post(url, data=payload)
        soup = BeautifulSoup(r.text, "html.parser")
        errs = soup.find_all(attrs={'class': 'dnserror'})
        if errs:
            raise AddError([e.text for e in errs], record, records)
        return len(soup.find_all(attrs={'class': 'dnssuccess'}))

    def update_record(self, record: Record, records: Optional[List[Record]] = None) -> int:
        url = self.manage_domain_url(record.domain)
        token = self._get_manage_domain_token(url)
        payload = {
            'dnsaction': 'modify',
            'token': token
        }

        if records is None:
            records = self.list_records(record.domain)
        for i, rec in enumerate(records):
            record_id = "records[%d]" % i
            if rec.name == record.name and rec.type == record.type:
                rec = record
            payload[record_id + "[line]"] = ""
            payload[record_id + "[type]"] = rec.type.name
            payload[record_id + "[name]"] = str(rec.name)
            payload[record_id + "[ttl]"] = str(rec.ttl)
            payload[record_id + "[value]"] = str(rec.target)

        r = self.session.post(url, data=payload)
        soup = BeautifulSoup(r.text, "html.parser")
        errs = soup.find_all(attrs={'class': 'dnserror'})
        if errs:
            raise UpdateError([e.text for e in errs], record, records)
        return len(soup.find_all(attrs={'class': 'dnssuccess'}))

    def remove_record(self, record: Record, records: Optional[List[Record]] = None, url=client_area_url) -> bool:
        if records is None:
            records = self.list_records(record.domain)
        if not self.contains_record(record, records):
            return False
        payload = {
            'managedns': record.domain.name,
            'page': None,
            'records': record.type.name,
            'dnsaction': 'delete',
            'name': record.name,
            'value': record.target,
            'line': None,
            'ttl': record.ttl,
            'priority': None,
            'weight': None,
            'port': None,
            'domainid': record.domain.id
        }
        r = self.session.get(url, params=payload)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        errs = soup.find_all(attrs={'class': 'dnserror'})
        if errs:
            raise UpdateError([e.text for e in errs], record, records)
        assert len(soup.find_all(attrs={'class': 'dnssuccess'})) == 1
        return True

    def contains_domain(self, domain: Domain, domains=None):
        if domains is None:
            domains = self.list_domains()
        return any(domain.id == d.id and domain.name == d.name for d in domains)

    def contains_record(self, record, records: Optional[List[Record]] = None):
        if records is None:
            records = self.list_records(record.domain)
        return any(record.name == rec.name and record.type == rec.type for rec in records)

    def __contains__(self, item):
        if isinstance(item, Domain):
            return self.contains_domain(item)
        if isinstance(item, Record):
            return self.contains_record(item)
        return False

    def rollback_update(self, records: List[Record]):
        if not records:
            return False
        url = self.manage_domain_url(records[0].domain)
        token = self._get_manage_domain_token(url)
        payload = {
            'dnsaction': 'modify',
            'token': token
        }
        for i, rec in enumerate(records):
            record_id = "records[%d]" % i
            payload[record_id + "[line]"] = ""
            payload[record_id + "[type]"] = rec.type.name
            payload[record_id + "[name]"] = str(rec.name)
            payload[record_id + "[ttl]"] = str(rec.ttl)
            payload[record_id + "[value]"] = str(rec.target)

        return bool(self.session.post(url, data=payload))

    @staticmethod
    def manage_domain_url(domain: Domain):
        return f"{client_area_url}?managedns={quote(domain.name)}&domainid={quote(domain.id)}"

    def is_logged_in(self, r: Optional[requests.Response] = None, url: str = client_area_url):
        if r is None:
            r = self.session.get(url)
            r.raise_for_status()
        return '<section class="greeting">' in r.text

    def _get_login_token(self, url: str = client_area_url):
        return self._get_token(url)

    def _get_domain_token(self, url: str = list_domain_url):
        return self._get_token(url)

    def _get_manage_domain_token(self, url: str):
        return self._get_token(url)

    def _get_token(self, url: str):
        r = self.session.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        token = soup.find("input", {'name': 'token'})
        assert token and token['value'], "there's no token on this page"
        return token['value']
