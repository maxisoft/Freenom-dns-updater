import datetime


class Domain(object):
    def __init__(self, name=""):
        self.name = name
        self._register_date = datetime.date.today()
        self._expire_date = datetime.date.today()
        self.state = ""
        self.type = ""
        self.id = -1

    @property
    def register_date(self):
        return self._register_date

    @register_date.setter
    def register_date(self, value):
        if isinstance(value, datetime.date):
            self._register_date = value
        elif isinstance(value, datetime.datetime):
            self.register_date = value.date()
        else:
            self.register_date = self.parse_date(value)

    @property
    def expire_date(self):
        return self._expire_date

    @expire_date.setter
    def expire_date(self, value):
        if isinstance(value, datetime.date):
            self._expire_date = value
        elif isinstance(value, datetime.datetime):
            self._expire_date = value.date()
        else:
            self._expire_date = self.parse_date(value)

    @staticmethod
    def parse_date(value):
        return datetime.datetime.strptime(value, '%Y-%m-%d').date()

    def __str__(self, *args, **kwargs):
        return "Domain({.name})".format(self)

    def __repr__(self, *args, **kwargs):
        return "<{}({.id})>".format(self.__class__.__name__, self)

    def __eq__(self, other):
        if not isinstance(other, Domain):
            return False
        if self.id != other.id:
            return False
        if self.name != other.name:
            return False
        if self.register_date != other.register_date:
            return False
        if self.expire_date != other.expire_date:
            return False
        if self.state != other.state:
            return False
        if self.type != other.type:
            return False
        return True





