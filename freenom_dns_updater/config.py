import pathlib

import yaml
import six
import ipaddress

from .record import Record, RecordType
from .domain import Domain
from copy import copy

from .get_my_ip import *


class Config(dict):
    def __init__(self, src="freenom.yml", **kwargs):
        super(Config, self).__init__(**kwargs)
        if isinstance(src, pathlib.Path):
            src = str(src)
        self.reload(src)
        self.file = src
        self._records = None

    def reload(self, src):
        if isinstance(src, dict):
            content = src
        elif hasattr(src, 'read'):
            content = yaml.safe_load(src)
        else:
            with open(src) as f:
                content = yaml.safe_load(f)
        self.clear()
        self.update(content)
        self._records = None

    def save(self, file=None):
        file = file or self.file
        if isinstance(file, six.string_types):
            with open(file, 'w') as f:
                yaml.dump(self, f)
            return True
        return False

    @property
    def login(self):
        return self['login']

    @property
    def password(self):
        return self['password']

    @property
    def records(self):
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
            except:
                ipv6 = None
        for rec in records:
            ret += self._parse_record(rec, str(ipv4), str(ipv6) if ipv6 else None)
        self._records = ret
        return ret

    def _parse_record(self, raw_record, ipv4, ipv6):
        assert isinstance(raw_record, dict)
        domain_name = raw_record['domain']
        assert isinstance(domain_name, six.string_types)
        domain_name.strip().lower()
        assert domain_name
        domain = Domain()
        domain.name = domain_name

        record = Record(domain=domain)
        optional_record = None

        tmp = raw_record.get('name')
        if tmp is not None:
            record.name = str(tmp)
            assert record.name

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
                    assert ipv6
                    record.target = ipv6
                elif record.type == RecordType.A:
                    assert ipv4
                    record.target = ipv4
            else:  # type not given
                record.type = RecordType.A
                record.target = ipv4
                if ipv6 is not None:
                    optional_record = copy(record)
                    optional_record.type = RecordType.AAAA
                    optional_record.target = ipv6
        return [record] if optional_record is None else [record, optional_record]
