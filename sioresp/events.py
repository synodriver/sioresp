from dataclasses import dataclass, field
import decimal
from typing import Union, Optional


class NeedMoreData:
    pass


@dataclass
class BaseEvent:
    pass


@dataclass
class String(BaseEvent):
    data: Union[bytes, bytearray]
    len: Optional[int] = None

    def __str__(self):
        return self.data.decode()

    def __bytes__(self):
        return bytes(self.data)


@dataclass
class ReplyError(BaseEvent, Exception):
    data: Union[bytes, bytearray]

    def __str__(self):
        return self.data.decode()

    def __bytes__(self):
        return bytes(self.data)


@dataclass
class Integer(BaseEvent):
    data: Union[bytes, bytearray]

    def __int__(self):
        return int(self.data.decode())


@dataclass
class Null(BaseEvent):
    pass


@dataclass
class Double(BaseEvent):
    data: Union[bytes, bytearray]

    def __float__(self):
        return float(self.data.decode())


@dataclass
class Boolean(BaseEvent):
    data: Union[bytes, bytearray]

    def __bool__(self):
        if bytes(self.data) == b"t":
            return True
        elif bytes(self.data) == b"f":
            return False


@dataclass
class BigNumber(BaseEvent):  # todo decimal?
    data: Union[bytes, bytearray]

    def __int__(self):
        return int(self.data.decode())


@dataclass
class Array(BaseEvent):
    len: int
    data: list = field(default_factory=list)


@dataclass
class Map(BaseEvent):
    len: int
    data: dict = field(default_factory=dict)


@dataclass
class Set(BaseEvent):
    len: int
    data: set = field(default_factory=set)


@dataclass
class Push(BaseEvent):
    len: int
    data: set = field(default_factory=list)


need_more_data = NeedMoreData()
