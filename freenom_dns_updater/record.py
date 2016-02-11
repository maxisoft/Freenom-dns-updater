from enum import Enum, unique
import six


class Record(object):
    def __init__(self):
        self.name = ''
        self._type = RecordType.A
        self._ttl = int()
        self.target = ''

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
            self.type = RecordType[value.strip().upper()]
        elif isinstance(value, int):
            self.type = RecordType(value)
        else:
            raise ValueError("bad type")

    def __str__(self, *args, **kwargs):
        return "Record({0.name}, {0.type.name} -> {0.target})".format(self)

    def __repr__(self, *args, **kwargs):
        return "<{0}({1.name}, {1.type.name})>".format(self.__class__.__name__, self)

    def __eq__(self, other):
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
        return True


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

