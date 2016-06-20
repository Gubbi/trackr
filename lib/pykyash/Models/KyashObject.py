from datetime import datetime
import math
import calendar

__author__ = 'vinuth'


class KyashObject(object):
    schema = {}

    def __init__(self, args=None, **kwargs):
        if args and isinstance(args, dict):
            self.set_values(**args)

        elif kwargs:
            self.set_values(**kwargs)

    def set_values(self, **kwargs):
        for key, value in kwargs.items():
            if key in self.schema:
                if isinstance(self.schema[key], list):
                    if isinstance(value, list):
                        values = []
                        for item in value:
                            values.append(self.objectify(self.schema[key][0], item))
                        setattr(self, key, values)
                    else:
                        if value:
                            ValueError("Invalid value given for " + key + " attribute.")
                else:
                    setattr(self, key, self.objectify(self.schema[key], value))
            else:
                setattr(self, key, value)

    def objectify(self, cls, value):
        if value is None:
            return None

        if isinstance(value, cls):
            return value

        if issubclass(cls, datetime):
            return dt(int(value))
        if issubclass(cls, bool):
            if value.lower() in ["false", "no", "0", "n"]:
                return False
            else:
                return bool(value)

        if issubclass(cls, int):
            return int(math.ceil(float(value)))

        return cls(value)

    def to_dict(self):
        dict_obj = {}

        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue

            if not isinstance(value, list):
                value = [value]

            val_list = []
            for item in value:
                if isinstance(item, KyashObject):
                    val_list.append(item.to_dict())
                elif isinstance(item, datetime):
                    val_list.append(ut(item))
                else:
                    val_list.append(item)

            dict_obj[key] = val_list[0] if len(val_list) == 1 else val_list

        return dict_obj


def dt(u):
    return datetime.utcfromtimestamp(u)


def ut(d):
    return calendar.timegm(d.timetuple())
