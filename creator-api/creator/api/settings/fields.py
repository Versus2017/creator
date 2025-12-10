import abc
import json
from datetime import datetime
from datetime import timedelta


class BaseField(metaclass=abc.ABCMeta):
    def __init__(self, default, *, name=None, desc=None, type=None):
        self.name = name
        self.default = default
        self.desc = desc
        self.type = type

    def after_get(self, item, key, value):
        return value

    @abc.abstractmethod
    def serialize(self, value):
        pass

    @abc.abstractmethod
    def deserialize(self, data):
        pass


class StringField(BaseField):
    def serialize(self, value):
        return str(value)

    def deserialize(self, data):
        return data


class BooleanField(BaseField):
    def serialize(self, value):
        return str(value).lower()

    def deserialize(self, data):
        return data.lower() in {'true', 'ok', 'yes', 't', '1'}


class IntegerField(BaseField):
    def serialize(self, value):
        return str(value)

    def deserialize(self, data):
        return int(data)


class PercentField(IntegerField):
    def after_get(self, item, key, value):
        return value / 100


class FloatField(BaseField):
    def serialize(self, value):
        return str(value)

    def deserialize(self, data):
        return float(data)


class TTLField(BaseField):
    def __init__(self, default=0, *, name=None,
                 offset_hours=0, format_='%Y-%m-%d %H:%M:%S.%f'):
        super().__init__(default, name=name)
        self.offset = timedelta(hours=offset_hours)
        self.format = format_

    def serialize(self, value):
        if isinstance(value, (int, float)):
            dt = datetime.utcnow() + timedelta(seconds=value) + self.offset
        elif isinstance(value, timedelta):
            dt = datetime.utcnow() + value + self.offset
        elif isinstance(value, datetime):
            dt = value
        else:
            dt = datetime.strptime(str(value), self.format)
        return dt.strftime(self.format)

    def deserialize(self, data):
        dt = datetime.strptime(data, self.format) - self.offset
        return (dt - datetime.utcnow()).total_seconds()


class TimeDeltaField(BaseField):
    def serialize(self, value):
        return str(value)

    def deserialize(self, data):
        return int(data)

    def after_get(self, item, key, value):
        return timedelta(seconds=value)


class JSONField(BaseField):
    def serialize(self, value):
        return json.dumps(value)

    def deserialize(self, data):
        return json.loads(data)
