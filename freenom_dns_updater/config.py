import ipaddress
import os
import pathlib
from copy import copy
from typing import List, Optional, TypeVar, Union

import six
import yaml

from .domain import Domain
from .encrypted_string import EncryptedString
from .get_my_ip import get_my_ipv4, get_my_ipv6
from .record import Record, RecordType

T = TypeVar('T')

if hasattr(os, 'getenvb'):
    def _getenvb(varname: str, value: T = None) -> Union[Optional[T], bytes]:
        return os.getenvb(varname.encode(), value)
else:
    def _getenvb(varname: str, value: T = None) -> Union[Optional[T], bytes]:
        res = os.getenv(varname, value)
        if res is value:
            return value
        return res.encode() if isinstance(res, str) else res


class Config(dict):
    def __init__(self, src="freenom.yml", **kwargs):
        super().__init__(**kwargs)
        if isinstance(src, pathlib.Path):
            src = str(src)
        self._records = None
        self._password: EncryptedString = EncryptedString(b"")
        self.reload(src)
        self.file = src

    def reload(self, src):
        if isinstance(src, dict):
            content = src
        elif hasattr(src, 'read'):
            content = yaml.safe_load(src)
        else:
            with open(src) as f:
                content = yaml.safe_load(f)
        self.clear()
        self._password = EncryptedString(content.pop("password", ""),
                                         key=_getenvb("FDU_KEY"),
                                         iv=_getenvb("FDU_IV")).ensure_encrypted()
        self.update(content)
        self._records = None

    def save(self, file=None):
        file = file or self.file
        if isinstance(file, six.string_types):
            with open(file, 'w') as f:
                d = dict(self)
                d["password"] = self._password.str()
                yaml.dump(d, f)
            return True
        return False

    @property
    def login(self) -> str:
        return self['login']

    @property
    def password(self) -> str:
        return self._password.str()

    def __eq__(self, other):
        if self.password != other.password:
            return False
        return super().__eq__(other)

    @property
    def records(self) -> List[Record]:
        if self._records is not None:
            return self._records

        records = self['record']
        if isinstance(records, dict):
            records = [records]
        ret = []
        ipv4 = None
        ipv6 = None
        if records:
            ipv4 = get_my_ipv4()
            try:
                ipv6 = get_my_ipv6()
            except Exception:
                ipv6 = None
        for rec in records:
            ret += self._parse_record(rec, str(ipv4), str(ipv6) if ipv6 else None)
        self._records = ret
        return ret

    def _parse_record(self, raw_record: dict, ipv4: Optional[str], ipv6: Optional[str]) -> List[Record]:
        domain_name = raw_record['domain']
        if not isinstance(domain_name, six.string_types):
            raise TypeError("domain's name must be a string")
        domain_name = domain_name.strip().lower()
        if not domain_name:
            raise ValueError("empty domain name")
        domain = Domain()
        domain.name = domain_name

        record = Record(domain=domain)
        optional_record = None

        tmp = raw_record.get('name')
        if tmp is not None:
            record.name = str(tmp)
            if not record.name:
                raise ValueError("empty record name")

        type_given = False
        if 'type' in raw_record:
            record.type = raw_record['type']
            type_given = True

        target_given = False
        tmp = raw_record.get('target')
        if tmp is not None:
            record.target = str(tmp).strip()
            target_given = True

        if 'ttl' in raw_record:
            record.ttl = raw_record['ttl']

        if target_given and record.target != 'auto':
            try:
                addr = ipaddress.ip_address(six.u(record.target))
            except ValueError:
                pass
            else:
                if isinstance(addr, ipaddress.IPv4Address):
                    if type_given:
                        if record.type == RecordType.AAAA:
                            raise ValueError("cannot use ipv4 for AAAA record")
                    else:
                        record.type = RecordType.A
                elif isinstance(addr, ipaddress.IPv6Address):
                    if type_given:
                        if record.type == RecordType.A:
                            raise ValueError("cannot use ipv6 for A record")
                    else:
                        record.type = RecordType.AAAA
        else:  # target not given or target is 'auto'
            if type_given:
                if record.type == RecordType.AAAA:
                    if not ipv6:
                        raise ValueError("empty ipv6")
                    record.target = ipv6
                elif record.type == RecordType.A:
                    if not ipv4:
                        raise ValueError("empty ipv4")
                    record.target = ipv4
            else:  # type not given
                if not ipv4:
                    raise ValueError("empty ipv4")
                record.type = RecordType.A
                record.target = ipv4
                if ipv6 is not None:
                    optional_record = copy(record)
                    optional_record.type = RecordType.AAAA
                    optional_record.target = ipv6
        return [record] if optional_record is None else [record, optional_record]
