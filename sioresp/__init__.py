from enum import Enum, auto
from collections import deque
from typing import Union, List, Tuple, Any, Sequence
from io import BytesIO

from sioresp.config import Config
from sioresp.buffer import Buffer
from sioresp.events import BaseEvent, String, VerbatimString, ReplyError, Integer, Array, Map, Set, Push, Double, \
    Attribute, Null, Boolean
from sioresp.exceptions import ProtocolError

try:
    import hiredis
except:
    hiredis = None

string_start = 43  # b"+"
error_start = 45  # b"-1"
integer_start = 58  # b":"
double_start = 44  # b","
null_start = 95  # b"_"

bulk_string_start = 36  # b"$"
array_start = 42  # b"*"
bool_start = 35  # b"#"
blob_error_start = 33  # b"!"
verbatim_string_start = 61  # b"="
big_number_start = 40  # b"("
map_start = 37  # b"%"
set_start = 126  # b'~'
attribute_start = 124  # struct  b"|"
push_start = 62

CRLF = b"\r\n"
VALID_START_BYTE = {33, 35, 36, 37, 40, 42, 43, 44, 45, 58, 61, 62, 95, 124, 126}


class ParserState(Enum):
    wait_data = auto()  # 现在还没有开始读取
    read_bulk_string_body = auto()
    read_blob_error_body = auto()
    read_verbatim_string_body = auto()


# https://erpeng.github.io/2019/07/12/redis-resp3/
# https://redis.com.cn/topics/protocol.html#:~:text=Redis%E5%8D%8F%E8%AE%AE%E8%AF%A6%E7%BB%86%E8%A7%84%E8%8C%83%20Redis%E5%AE%A2%E6%88%B7%E7%AB%AF%E5%92%8C%E6%9C%8D%E5%8A%A1%E5%99%A8%E7%AB%AF%E9%80%9A%E4%BF%A1%E4%BD%BF%E7%94%A8%E5%90%8D%E4%B8%BA%20RESP%20%28REdis%20Serialization,Protocol%29%20%E7%9A%84%E5%8D%8F%E8%AE%AE%E3%80%82%20%E8%99%BD%E7%84%B6%E8%BF%99%E4%B8%AA%E5%8D%8F%E8%AE%AE%E6%98%AF%E4%B8%93%E9%97%A8%E4%B8%BARedis%E8%AE%BE%E8%AE%A1%E7%9A%84%EF%BC%8C%E5%AE%83%E4%B9%9F%E5%8F%AF%E4%BB%A5%E7%94%A8%E5%9C%A8%E5%85%B6%E5%AE%83%20client-server%20%E9%80%9A%E4%BF%A1%E6%A8%A1%E5%BC%8F%E7%9A%84%E8%BD%AF%E4%BB%B6%E4%B8%8A%E3%80%82
# https://www.zeekling.cn/articles/2021/01/10/1610263628832.html#b3_solo_h3_16

class Connection:
    post_processors = {
        String: lambda x: bytes(x) if x.len is None else None,  # len不是None就是-1 这里把-1长度的str也视为None
        VerbatimString: lambda x: bytes(x) if x.len is None else None,
        ReplyError: lambda x: x,
        Integer: lambda x: int(x),
        Double: lambda x: float(x),
        Boolean: lambda x: bool(x),
        Null: lambda x: None
    }

    def __init__(self, config: Config):
        self.config = config
        self._buffer = Buffer()
        self._events = deque()
        self._events_backup = deque()  # stack
        self._parser_state = ParserState.wait_data
        self._current_length = None  # type: Optional[int]

    def feed_data(self, data: Union[bytes, bytearray]) -> None:
        assert data, "no data at all"
        self._buffer.extend(data)

        while True:
            start = self._buffer[0]
            if start not in VALID_START_BYTE:
                raise ProtocolError(f"invalid start byte {chr(start)}")
            if self._parser_state == ParserState.wait_data:
                if start == string_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = String(data=s)
                    self._events.append(event)
                if start == error_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = ReplyError(data=s)
                    self._events.append(event)
                if start == integer_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = Integer(data=s)
                    self._events.append(event)
                if start == big_number_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = Integer(data=s)
                    self._events.append(event)
                if start == bulk_string_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    length = int(s.decode())
                    if length < 0:
                        event = String(data=b"", len=length)
                        self._events.append(event)
                    else:
                        self._current_length = length
                        self._parser_state = ParserState.read_bulk_string_body
                if start == blob_error_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    length = int(s.decode())
                    if length < 0:
                        event = ReplyError(data=b"", len=length)
                        self._events.append(event)
                    else:
                        self._current_length = length
                        self._parser_state = ParserState.read_blob_error_body
                if start == verbatim_string_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    length = int(s.decode())
                    if length < 0:
                        event = VerbatimString(data=b"", len=length)
                        self._events.append(event)
                    else:
                        self._current_length = length
                        self._parser_state = ParserState.read_verbatim_string_body
                if start == double_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = Double(data=s)  # fixme inf -inf
                    self._events.append(event)
                if start == null_start:
                    s = self._buffer.readline()
                    if s is None:
                        break
                    s.skip(1)
                    if len(s) != 0:
                        raise ProtocolError("null can't contain any data")
                    event = Null()
                    self._events.append(event)
                if start == bool_start:
                    s = self._buffer.readline()
                    if s is None:
                        break
                    s.skip(1)
                    if bytes(s) not in (b"t", b"f"):
                        raise ProtocolError("bool must be t or f")
                    event = Boolean(data=s)
                    self._events.append(event)
                if start == array_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = Array(len=int(s.decode()))
                    self._events.append(event)
                if start == map_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = Map(len=int(s.decode()))
                    self._events.append(event)
                if start == set_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = Set(len=int(s.decode()))
                    self._events.append(event)
                if start == attribute_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = Attribute(len=int(s.decode()))
                    self._events.append(event)
                if start == push_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = Push(len=int(s.decode()))
                    self._events.append(event)

            if self._parser_state == ParserState.read_bulk_string_body:
                if len(self._buffer) < self._current_length + 2:
                    break
                s = self._buffer.read(self._current_length)
                if bytes(self._buffer.read(2)) != b"\r\n":
                    raise ProtocolError("bulk string should ended with \\r\\n")
                self._current_length = None  # reset长度
                event = String(data=s)
                self._parser_state = ParserState.wait_data
                self._events.append(event)

            if self._parser_state == ParserState.read_verbatim_string_body:
                if len(self._buffer) < self._current_length + 2:
                    break
                s = self._buffer.read(self._current_length)
                if bytes(self._buffer.read(2)) != b"\r\n":
                    raise ProtocolError("verbatim string should ended with \\r\\n")
                self._current_length = None  # reset长度
                type_, _, data = s.partition(b":")
                event = VerbatimString(data=data, type=type_)
                self._parser_state = ParserState.wait_data
                self._events.append(event)

            if self._parser_state == ParserState.read_blob_error_body:
                if len(self._buffer) < self._current_length + 2:
                    break
                s = self._buffer.read(self._current_length)
                if bytes(self._buffer.read(2)) != b"\r\n":
                    raise ProtocolError("blob error should ended with \\r\\n")
                self._current_length = None  # reset长度
                event = ReplyError(data=s)
                self._parser_state = ParserState.wait_data
                self._events.append(event)

            if not self._buffer:
                break

    def reset(self):
        self._buffer.clear()
        self._events.clear()
        self._events_backup.clear()
        self._parser_state = ParserState.wait_data

    def _next_element(self):
        event = self._events.popleft()
        self._events_backup.append(event)

        if isinstance(event, Array):
            return self._next_array(event.len)
        elif isinstance(event, Set):
            return self._next_set(event.len)
        elif isinstance(event, Map):
            return self._next_map(event.len)
        elif isinstance(event, Attribute):
            return self._next_attribute(event.len)
        elif isinstance(event, Push):
            return self._next_push(event.len)

        return self.post_processors[type(event)](event)

    def _next_array(self, len_: int) -> list:
        l = []
        if len_ < 0:  # 长度为-1的array解析成None
            l = None
        else:
            for _ in range(len_):
                l.append(self._next_element())
        return l

    def _next_set(self, len_: int) -> set:
        return {self._next_element() for _ in range(len_)}

    def _next_map(self, len_: int) -> Union[List[Tuple], dict]:
        if self.config.dict_for_map:
            m = {}
            for _ in range(len_):
                k = self._next_element()
                v = self._next_element()
                m[k] = v
        else:
            m = []  # List[Tuple[K, V]] cause redis could use something unhashable as key
            for _ in range(len_):
                k = self._next_element()
                v = self._next_element()
                m.append((k, v))
        return m

    def _next_attribute(self, len_: int) -> List[Tuple]:
        m = []  # attribute当成map处理
        for _ in range(len_):
            k = self._next_element()
            v = self._next_element()
            m.append((k, v))
        return m

    def _next_push(self, len_: int) -> list:
        l = []
        if len_ < 0:  # 长度为-1的array解析成None
            l = None
        else:
            for _ in range(len_):
                l.append(self._next_element())
        return l

    def __iter__(self):
        return self

    def __next__(self):
        try:
            ele = self._next_element()
            self._events_backup.clear()  # 没出事
            return ele
        except IndexError:
            while self._events_backup:  # 出事了 不够数据 恢复栈
                event = self._events_backup.pop()
                self._events.appendleft(event)
            raise StopIteration

    def pack_string(self, string: Union[str, bytes, bytearray]) -> bytes:
        return f"+{string}\r\n".encode(self.config.encoding,
                                       self.config.errors) if isinstance(string, str) else b"+%s\r\n" % string

    def pack_bulk_string(self, string: Union[str, bytes, bytearray]) -> bytes:
        if isinstance(string, str):
            string = string.encode(self.config.encoding, self.config.errors)
        return b"$%d\r\n%s\r\n" % (len(string), string)

    def pack_error(self, err: Union[str, bytes, bytearray]) -> bytes:
        return f"-{err}\r\n".encode(self.config.encoding,
                                    self.config.errors) if isinstance(err, str) else b"-%s\r\n" % err

    def pack_integer(self, ele: int) -> bytes:
        return f":{ele}\r\n".encode(self.config.encoding, self.config.errors)

    def pack_double(self, ele: float) -> bytes:
        """
        resp 3
        :param ele:
        :return:
        """
        return b",%s\r\n" % str(ele).encode()

    def pack_boolean(self, ele: bool) -> bytes:
        """
        resp 3
        :param ele:
        :return:
        """
        return b"#t\r\n" if ele else b"#f\r\n"

    def pack_blob_error(self, err: Union[str, bytes, bytearray]) -> bytes:
        """
        resp 3
        :param err:
        :return:
        """
        if isinstance(err, str):
            err = err.encode(self.config.encoding, self.config.errors)
        return b"!%d\r\n%s\r\n" % (len(err), err)

    def pack_verbatim_string(self, type_: Union[str, bytes, bytearray],
                             string: Union[str, bytes, bytearray]) -> bytes:
        """
        resp 3
        :param type_:
        :param string:
        :return:
        """
        if isinstance(string, str):
            string = string.encode(self.config.encoding, self.config.errors)
        if isinstance(type_, str):
            type_ = type_.encode(self.config.encoding, self.config.errors)
        string = type_ + b":" + string
        return b"=%d\r\n%s\r\n" % (len(string), string)

    def pack_big_number(self, number: Union[int, str, bytes, bytearray]) -> bytes:
        """
        resp 3
        :param number:
        :return:
        """
        if isinstance(number, int):
            return b"(%d\r\n" % number
        elif isinstance(number, str):
            number = number.encode(self.config.encoding, self.config.errors)
        return b"(%s\r\n" % number

    def pack_null(self) -> bytes:
        return b"$-1\r\n" if self.config.resp_version == 2 else b"_\r\n"

    def pack_array(self, arr: Union[List, Tuple]) -> bytes:
        ret = BytesIO()
        ret.write(b"*%d\r\n" % len(arr))  # arr's len prefix
        for i in arr:
            ret.write(self.pack_element(i))
        return ret.getvalue()

    def pack_map(self, map: Union[dict, Sequence[Tuple[Any, Any]]]) -> bytes:
        """
        resp 3
        :param map:
        :return:
        """
        ret = BytesIO()
        ret.write(b"%")
        ret.write(b"%d\r\n" % len(map))
        if isinstance(map, dict):
            map = map.items()
        for k, v in map:
            ret.write(self.pack_element(k))
            ret.write(self.pack_element(v))
        return ret.getvalue()

    def pack_set(self, ele: set) -> bytes:
        """
        resp 3
        :param ele:
        :return:
        """
        ret = BytesIO()
        ret.write(b"~%d\r\n" % len(ele))
        for i in ele:
            ret.write(self.pack_element(i))
        return ret.getvalue()

    def pack_attribute(self, attr: Union[dict, Sequence[Tuple[Any, Any]]]) -> bytes:
        """
        resp 3
        :param attr:
        :return:
        """
        ret = BytesIO()
        ret.write(b"|%d\r\n" % len(attr))
        if isinstance(attr, dict):
            attr = attr.items()
        for k, v in attr:
            ret.write(self.pack_element(k))
            ret.write(self.pack_element(v))
        return ret.getvalue()

    def pack_push(self, push: Union[List, Tuple]) -> bytes:
        """
        resp 3
        :param push: like that in array
        :return:
        """
        if self.config.resp_version == 2:
            raise ProtocolError("resp version2 doesn't support push type")
        ret = BytesIO()
        ret.write(b">%d\r\n" % len(push))  # push's len prefix
        for i in push:
            ret.write(self.pack_element(i))
        return ret.getvalue()

    def pack_element(self, ele: Any) -> bytes:
        """
        this method could be rewrite in subclasses to have different strategies
        :param ele:
        :return:
        """
        if isinstance(ele, (str, bytes, bytearray)):
            return self.pack_bulk_string(ele)
        elif isinstance(ele, int):
            if self.config.resp_version == 2:
                return self.pack_integer(ele)
            else:
                return self.pack_big_number(ele)
        elif isinstance(ele, float):
            if self.config.resp_version == 2:
                return self.pack_string(str(ele))
            else:
                return self.pack_double(ele)
        elif isinstance(ele, bool):
            if self.config.resp_version == 3:
                return self.pack_boolean(ele)
            else:
                raise ProtocolError("resp version2 doesn't support bool type")
        elif isinstance(ele, (list, tuple)):
            return self.pack_array(ele)
        elif isinstance(ele, dict):
            if self.config.resp_version == 3:
                return self.pack_map(ele)
            else:
                raise ProtocolError("resp version2 doesn't support map type")
        elif isinstance(ele, set):
            if self.config.resp_version == 3:
                return self.pack_set(ele)
            else:
                raise ProtocolError("resp version2 doesn't support set type")
        elif ele is None:
            return self.pack_null()

    def send_command(self, *cmd) -> bytes:
        return self.pack_element(cmd[0]) if len(cmd) == 1 else self.pack_element(cmd)


if hiredis is not None:
    class HiredisConnection(Connection):
        def __init__(self, config: Config):
            self.config = config
            self.reader = hiredis.Reader(ProtocolError, ReplyError, notEnoughData=StopIteration)

        def feed_data(self, data: Union[bytes, bytearray]) -> None:
            self.reader.feed(data)

        def __next__(self):
            data = self.reader.gets()
            if data is StopIteration:
                raise data
            return data

        def reset(self):
            pass
