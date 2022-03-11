from dataclasses import dataclass, field
import decimal
from typing import Union, Optional


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
class VerbatimString(String):
    type: Optional[str] = None


@dataclass
class ReplyError(BaseEvent):
    data: Union[bytes, bytearray, str]
    len: Optional[int] = None

    def __str__(self):
        return self.data if isinstance(self.data, str) else self.data.decode()

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


@dataclass
class Map(BaseEvent):
    len: int


@dataclass
class Set(BaseEvent):
    len: int


@dataclass
class Attribute(BaseEvent):
    len: int


@dataclass
class Push(BaseEvent):
    len: int
