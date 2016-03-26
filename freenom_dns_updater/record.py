from enum import Enum, unique

import six

from .domain import Domain


@unique
class RecordType(Enum):
    A = 1
    AAAA = 2
    CNAME = 3
    LOC = 4
    MX = 5
    NAPTR = 6
    RP = 7
    TXT = 8


class Record(object):
    def __init__(self, name='', type=RecordType.A, ttl=14440, target='', domain=None):
        self._name = None
        self._type = None
        self._ttl = None
        self._domain = None
        self._index = None
        self.name = name
        self.type = type
        self.ttl = ttl
        self.target = target
        self.domain = domain

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = str(value).strip().upper()

    @property
    def ttl(self):
        return self._ttl

    @ttl.setter
    def ttl(self, value):
        self._ttl = int(value)

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, value):
        if isinstance(value, RecordType):
            self._type = value
        elif isinstance(value, six.string_types):
            self._type = RecordType[value.strip().upper()]
        elif isinstance(value, int):
            self._type = RecordType(value)
        else:
            raise ValueError("bad type")

    @property
    def domain(self):
        return self._domain

    @domain.setter
    def domain(self, value):
        if value is None or isinstance(value, Domain):
            self._domain = value
        else:
            raise ValueError("bad type")

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, value):
        self._index = value

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
        if self.domain != other.domain:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)


