import datetime


class Domain(object):
    def __init__(self, name=""):
        self.name: str = name
        self._register_date = datetime.date.today()
        self._expire_date = datetime.date.today()
        self.state: str = ""
        self.type: str = ""
        self._id: str = ""

    @property
    def register_date(self) -> datetime.date:
        return self._register_date

    @register_date.setter
    def register_date(self, value):
        if isinstance(value, datetime.date):
            self._register_date = value
        elif isinstance(value, datetime.datetime):
            self._register_date = value.date()
        else:
            self.register_date = self.parse_date(value)

    @property
    def expire_date(self) -> datetime.date:
        return self._expire_date

    @expire_date.setter
    def expire_date(self, value):
        if isinstance(value, datetime.date):
            self._expire_date = value
        elif isinstance(value, datetime.datetime):
            self._expire_date = value.date()
        else:
            self._expire_date = self.parse_date(value)

    @property
    def id(self) -> str:
        return self._id

    @id.setter
    def id(self, value):
        self._id = str(value)

    @staticmethod
    def parse_date(value) -> datetime.date:
        try:
            return datetime.datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return datetime.datetime.strptime(value, '%d/%m/%Y').date()

    def __str__(self, *args, **kwargs):
        return "Domain({.name})".format(self)

    def __repr__(self, *args, **kwargs):
        return "<{}({.id})>".format(self.__class__.__name__, self)

    def __eq__(self, other):
        if self is other:
            return True
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

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.id)
