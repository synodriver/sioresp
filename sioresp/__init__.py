from enum import Enum, auto
from collections import deque
from typing import Union

from sioresp.config import Config
from sioresp.buffer import Buffer
from sioresp.events import BaseEvent, String, ReplyError, Integer, Array, need_more_data
from sioresp.exceptions import ProtocolError

try:
    import hiredis
    import redis
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


class ParserState(Enum):
    wait_data = auto()  # 现在还没有开始读取
    read_bulk_string_body = auto()


# def parse_string(x: String):
#     if x.len is None:
#         return str(x)
#     else:
#         return None


class Connection:
    post_processors = {
        String: lambda x: bytes(x) if x.len is None else None,  # len不是None就是-1 这里把-1长度的str也视为None
        ReplyError: lambda x: x,
        Integer: lambda x: int(x)
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
            if self._parser_state == ParserState.wait_data:
                if start == string_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = String(data=s)
                    self._events.append(event)
                    self._events_backup.append(event)
                if start == error_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = ReplyError(data=s)
                    self._events.append(event)
                    self._events_backup.append(event)
                if start == integer_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = Integer(data=s)
                    self._events.append(event)
                    self._events_backup.append(event)
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
                        self._events_backup.append(event)
                    else:
                        self._current_length = length
                        self._parser_state = ParserState.read_bulk_string_body
                if start == array_start:
                    s = self._buffer.readline()
                    if s is not None:
                        s.skip(1)
                    else:
                        break
                    event = Array(len=int(s.decode()))
                    self._events.append(event)
                    self._events_backup.append(event)

            if self._parser_state == ParserState.read_bulk_string_body:
                if len(self._buffer) < self._current_length + 2:
                    break
                s = self._buffer.read(self._current_length)
                if bytes(self._buffer.read(2)) != b"\r\n":
                    raise ProtocolError("bulk string should be ended with \\r\\n")
                self._current_length = None  # reset长度
                event = String(data=s)
                self._parser_state = ParserState.wait_data
                self._events.append(event)
                self._events_backup.append(event)
            if not self._buffer:
                break

    def reset(self):
        self._buffer.clear()
        self._events.clear()
        self._events_backup.clear()
        self._parser_state = ParserState.wait_data

    def next_element(self):
        # events_backup = self._events.copy()
        try:
            event = self._events.popleft()
            self._events_backup.append(event)
            if isinstance(event, String):
                event = self.post_processors[String](event)
            elif isinstance(event, ReplyError):
                event = self.post_processors[ReplyError](event)
            elif isinstance(event, Integer):
                event = self.post_processors[Integer](event)
            elif isinstance(event, Array):
                event = self.next_array(event.len)

            if isinstance(event, Exception):
                raise event
            else:
                return event
        except IndexError:
            event = self._events_backup.pop()
            self._events.appendleft(event)
            raise

    def next_array(self, len_: int):
        l = []
        if len_ < 0:  # 长度为-1的array解析成None
            l = None
        else:
            for i in range(len_):
                l.append(self.next_element())
        return l

    def send_command(self, *cmd) -> bytes:
        pass


class HiredisConnection(Connection):
    pass
