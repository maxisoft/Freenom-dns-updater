from enum import Enum, unique
from typing import Optional

from .domain import Domain


@unique
class RecordType(Enum):
    INVALID = 0
    A = 1
    AAAA = 2
    CNAME = 3
    LOC = 4
    MX = 5
    NAPTR = 6
    RP = 7
    TXT = 8


class Record(object):
    def __init__(self, name='', type=RecordType.A, ttl=14440, target: str = '', domain=None):
        self._name = ''
        self._type = RecordType.INVALID
        self._ttl = -1
        self._domain: Optional[Domain] = None
        self.name = name
        self.type = type
        self.ttl = ttl
        self.target = target
        if domain is not None:
            self.domain = domain

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value):
        self._name = str(value).strip().upper()

    @property
    def ttl(self) -> int:
        return self._ttl

    @ttl.setter
    def ttl(self, value):
        self._ttl = int(value)

    @property
    def type(self) -> RecordType:
        assert self._type != RecordType.INVALID  # nosec
        return self._type

    @type.setter
    def type(self, value):
        if isinstance(value, RecordType):
            self._type = value
        elif isinstance(value, str):
            self._type = RecordType[value.strip().upper()]
        elif isinstance(value, int):
            self._type = RecordType(value)
        else:
            raise ValueError("bad type")

    @property
    def domain(self) -> Domain:
        assert self._domain is not None  # nosec
        return self._domain

    @domain.setter
    def domain(self, value):
        if isinstance(value, Domain):
            self._domain = value
        else:
            raise TypeError(f"bad type {type(value)}")

    def has_domain(self) -> bool:
        return self._domain is not None

    def __str__(self, *args, **kwargs):
        return "Record({0.name}, {0.type.name} -> {0.target})".format(self)

    def __repr__(self, *args, **kwargs):
        return "<{0}({1.name}, {1.type.name})>".format(self.__class__.__name__, self)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Record):
            return False
        if self.name != other.name:
            return False
        if self.type != other.type:
            return False
        if self.ttl != other.ttl:
            return False
        if self.target != other.target:
            return False
        if self._domain != other._domain:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)
