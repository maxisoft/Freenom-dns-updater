import datetime
import warnings
from typing import Dict, List, Optional, Union
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .domain import Domain
from .domain_parser import DomainParser
from .exception import AddError, RemoveError, UpdateError
from .freenom_session import FreenomSession
from .record import Record
from .record_parser import RecordParser

DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko"
FREENOM_BASE_URL = 'https://my.freenom.com'

PARSED_FREENOM_BASE_URL = urlparse(FREENOM_BASE_URL)
LOGIN_URL = urljoin(FREENOM_BASE_URL, 'dologin.php')
CLIENT_AREA_URL = urljoin(FREENOM_BASE_URL, 'clientarea.php')
LIST_DOMAIN_URL = f'{CLIENT_AREA_URL}?action=domains'
DOMAIN_FORWARD_URL = f'{CLIENT_AREA_URL}?action=domaindetails'


HttpParamDict = Dict[str, Union[None, str, int, float]]


class Freenom(object):
    def __init__(self, user_agent: str = DEFAULT_USER_AGENT):
        self.session: requests.Session = FreenomSession()
        self.session.headers.update({'User-Agent': user_agent, "Accept-Language": "en-US,en;q=0.5"})

    def __del__(self):
        self.session.close()

    def login(self, login: str, password: str, url: str = LOGIN_URL) -> bool:
        token = self._get_login_token()
        payload = {'token': token,
                   'username': login,
                   'password': password,
                   'rememberme': ''}
        host_name = urlparse(url).hostname
        if host_name != PARSED_FREENOM_BASE_URL.hostname:
            warnings.warn(f"Using another host than {PARSED_FREENOM_BASE_URL.hostname} is not tested")
        r = self.session.post(url, payload,
                              headers={'Host': host_name, 'Referer': f'https://{host_name}/clientarea.php'})
        r.raise_for_status()
        return self.is_logged_in(r)

    def list_domains(self, url: str = LIST_DOMAIN_URL) -> List[Domain]:
        token = self._get_domain_token()
        payload: HttpParamDict = {'token': token, 'itemlimit': 'all'}
        r = self.session.post(url, payload)
        r.raise_for_status()
        return DomainParser.parse(r.text)

    def current_url_forward(self, id_):
        url = DOMAIN_FORWARD_URL + "&id="+str(id_)+"&modop=custom&a=urlforwarding"
        token = self._get_domain_token(url)
        payload: HttpParamDict = {'token': token}
        r = self.session.post(url, payload)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        urlelem = soup.find("input", {'id': 'url'})
        modeelem = soup.find("option", {"selected": "selected"})
        if not urlelem or not modeelem:
            raise ValueError("can't parse the given html")
        forwardurl = urlelem["value"]
        mode = modeelem["value"]
        return forwardurl, mode

    def change_url_forward(self, id_, newurl, mode, url: str = DOMAIN_FORWARD_URL):
        token = self._get_token(url)
        payload: HttpParamDict = {'token': token}
        payload["id"] = str(id_)
        payload["modop"] = "custom"
        payload["a"] = "urlforwarding"
        payload["save"] = "true"
        payload["url"] = str(newurl)
        payload["mode"] = str(mode)
        r = self.session.post(url, payload)

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
        payload: HttpParamDict = {
            'dnsaction': 'add',
            'token': token
        }
        record_id = f"addrecord[{0:d}]"
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
        payload: HttpParamDict = {
            'dnsaction': 'modify',
            'token': token
        }

        if records is None:
            records = self.list_records(record.domain)
        for i, rec in enumerate(records):
            record_id = f"records[{i:d}]"
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

    def remove_record(self, record: Record, records: Optional[List[Record]] = None, url=CLIENT_AREA_URL) -> bool:
        if records is None:
            records = self.list_records(record.domain)
        if not self.contains_record(record, records):
            raise RemoveError(f"{record.name} not found in records of {record.domain.name}", record, records)

        payload: HttpParamDict = {'managedns': record.domain.name, 'domainid': record.domain.id}
        r = self.session.get(url, params=payload)
        r.raise_for_status()

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
        if len(soup.find_all(attrs={'class': 'dnssuccess'})) != 1:
            raise RemoveError("didn't found success message in the html page", record, records)
        return True

    def get_matching_domain(self, domain: Domain, domains=None) -> Optional[Domain]:
        if domains is None:
            domains = self.list_domains()
        return next((d for d in domains if domain.id == d.id and domain.name == d.name), None)

    def contains_domain(self, domain: Domain, domains=None):
        return self.get_matching_domain(domain, domains) is not None

    def get_matching_record(self, record, records: Optional[List[Record]] = None) -> Optional[Record]:
        if records is None:
            records = self.list_records(record.domain)
        return next((rec for rec in records if record.name == rec.name and record.type == rec.type), None)

    def contains_record(self, record: Record, records: Optional[List[Record]] = None):
        return self.get_matching_record(record, records) is not None

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
        payload: HttpParamDict = {
            'dnsaction': 'modify',
            'token': token
        }
        for i, rec in enumerate(records):
            record_id = f"records[{i:d}]"
            payload[record_id + "[line]"] = ""
            payload[record_id + "[type]"] = rec.type.name
            payload[record_id + "[name]"] = str(rec.name)
            payload[record_id + "[ttl]"] = str(rec.ttl)
            payload[record_id + "[value]"] = str(rec.target)

        return bool(self.session.post(url, data=payload))

    @staticmethod
    def manage_domain_url(domain: Domain):
        return urljoin(FREENOM_BASE_URL, f"clientarea.php?managedns={quote(domain.name)}&domainid={quote(domain.id)}")

    def need_renew(self, domain):
        return domain and domain.expire_date - datetime.date.today() <= datetime.timedelta(days=13)

    def renew(self, domain, period: int = 12, url=FREENOM_BASE_URL + '/domains.php?submitrenewals=true'):
        if period not in range(1, 13):
            raise ValueError("period not in (1, 12)")
        if self.need_renew(domain):
            # keep this request to simulate humain usage and get token
            token = self._get_renew_token(domain)
            payload = {'token': token,
                       'renewalid': f"{domain.id}",
                       f'renewalperiod[{domain.id}]': f"{period}M",
                       'paymentmethod': 'credit'
                       }
            headers = {'Referer': urljoin(FREENOM_BASE_URL, f"domains.php?a=renewdomain&domain={quote(domain.id)}")}
            r = self.session.post(url, payload, headers=headers)
            r.raise_for_status()
            return 'Order Confirmation' in r.text
        return False

    def set_nameserver(self, domain, ns):
        if domain is None:
            return False
        url = urljoin(FREENOM_BASE_URL, f'clientarea.php?action=domaindetails&id={quote(domain.id)}')
        i = 1
        token = self._get_set_ns_token(domain)
        params: HttpParamDict = {
            'id': domain.id,
            'token': token,
            'sub': 'savens',
            'nschoice': 'custom'
        }
        for e in ns:
            params[f'ns{i}'] = e
            i += 1
        while i <= 5:
            params[f'ns{i}'] = ''
            i += 1
        headers = {'Referer': url}
        r = self.session.post(url, params, headers=headers)
        r.raise_for_status()
        return 'Changes Saved Successfully!' in r.text

    def is_logged_in(self, r: Optional[requests.Response] = None, url: str = CLIENT_AREA_URL):
        if r is None:
            r = self.session.get(url)
            r.raise_for_status()
        return '<section class="greeting">' in r.text

    def _get_login_token(self, url: str = CLIENT_AREA_URL):
        return self._get_token(url)

    def _get_domain_token(self, url: str = LIST_DOMAIN_URL):
        return self._get_token(url)

    def _get_manage_domain_token(self, url: str):
        return self._get_token(url)

    def _get_renew_token(self, domain, url=FREENOM_BASE_URL + "/domains.php?a=renewdomain&domain={0.id}"):
        return self._get_token(url.format(domain))

    def _get_set_ns_token(self, domain, url=FREENOM_BASE_URL + "/clientarea.php?action=domaindetails&domain={0.id}"):
        return self._get_token(url.format(domain))

    def _get_token(self, url: str):
        r = self.session.get(url)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        token = soup.find("input", {'name': 'token'})
        if not token or not token['value']:
            raise RuntimeError("there's no token on this page")
        return token['value']
