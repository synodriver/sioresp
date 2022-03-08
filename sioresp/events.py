from dataclasses import dataclass, field
from typing import Union


class NeedMoreData:
    pass


@dataclass
class Result:
    data: Union[bytes, bytearray]

    def __repr__(self):
        rep = "%s: %s " % (type(self).__name__, self.data)
        return rep


@dataclass
class String(Result):
    def __str__(self):
        return self.data.decode()

    def __bytes__(self):
        return bytes(self.data)


@dataclass
class ReplyError(Result, Exception):
    def __str__(self):
        return self.data.decode()


@dataclass
class Integer(Result):
    def __int__(self):
        return int(self.data.decode())


@dataclass
class Null(Result):
    pass


@dataclass
class Double(Result):
    pass


@dataclass
class Boolean(Result):
    pass


@dataclass
class BigNumber(Result):
    pass


@dataclass
class Array(Result, list):
    data: bytes = field(default=None, init=False)
    len: int = None


@dataclass
class Map(Result):
    pass


@dataclass
class Set(Result):
    pass


@dataclass
class Push(Result):
    pass


need_more_data = NeedMoreData()
