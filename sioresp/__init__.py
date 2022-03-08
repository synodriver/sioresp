from enum import Enum, auto

from sioresp.config import Config
from sioresp.buffer import Buffer
from sioresp.events import Result, String, ReplyError, Integer, Array
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
# todo
push_start = 0
hello_start = 0

CRLF = b"\r\n"


class ParserState(Enum):
    wait_data = auto()  # 现在还没有开始读取
    read_string = auto()
    read_error = auto()
    read_integer = auto()
    read_bulk_string_len = auto()
    read_bulk_string_body = auto()
    read_array_len = auto()
    read_array_body = auto()


class Connection:
    def __init__(self, config: Config):
        self.config = config
        self._buffer = Buffer()
        self._parser_states = [ParserState.wait_data]
        self._current_lengths = [None]
        self._current_ret = []

    def feed_data(self, data: bytes):
        assert data, "no data at all"
        self._buffer.extend(data)

        def parse(_ret: list) -> None:
            if self._parser_states[-1] == ParserState.wait_data:
                if self._buffer[0] == string_start:
                    self._parser_states[-1] = ParserState.read_string
                if self._buffer[0] == error_start:
                    self._parser_states[-1] = ParserState.read_error
                if self._buffer[0] == integer_start:
                    self._parser_states[-1] = ParserState.read_integer
                if self._buffer[0] == bulk_string_start:
                    self._parser_states[-1] = ParserState.read_bulk_string_len
                if self._buffer[0] == array_start:
                    self._parser_states[-1] = ParserState.read_array_len
                del self._buffer[0]
                return parse(_ret)
            if self._parser_states[-1] == ParserState.read_string:
                s = self._buffer.readline()
                if s is not None:
                    _ret.append(String(data=s))
                    self._parser_states[-1] = ParserState.wait_data
                return
            if self._parser_states[-1] == ParserState.read_error:
                s = self._buffer.readline()
                if s is not None:
                    _ret.append(ReplyError(data=s))
                    self._parser_states[-1] = ParserState.wait_data
                return
            if self._parser_states[-1] == ParserState.read_integer:
                s = self._buffer.readline()
                if s is not None:
                    _ret.append(Integer(data=s))
                    self._parser_states[-1] = ParserState.wait_data
                return
            if self._parser_states[-1] == ParserState.read_bulk_string_len:
                length = self._buffer.readline()
                if length is None:  # 长度不够 读不出来
                    return
                self._current_lengths[-1] = int(length.decode())  # 字符串长度
                self._parser_states[-1] = ParserState.read_bulk_string_body
                return parse(_ret)
            if self._parser_states[-1] == ParserState.read_bulk_string_body:
                if self._current_lengths[-1] < 0:
                    _ret.append(None)
                    self._parser_states[-1] = ParserState.wait_data
                    return
                if len(self._buffer) < self._current_lengths[-1] + 2:
                    return
                s = self._buffer.read(self._current_lengths[-1])
                if bytes(self._buffer.read(2)) != b"\r\n":
                    raise ProtocolError("expect \\r\\n at the end of bulk string")
                _ret.append(String(data=s))
                self._parser_states[-1] = ParserState.wait_data
                return
            if self._parser_states[-1] == ParserState.read_array_len:
                length = self._buffer.readline()
                if length is None:  # 长度不够 读不出来
                    return
                self._current_lengths[-1] = int(length.decode())  # 字符串长度
                self._parser_states[-1] = ParserState.read_array_body
                return parse(_ret)
            if self._parser_states[-1] == ParserState.read_array_body:
                tmp = Array()
                # 保存当前状态机
                buffer_copy = bytes(self._buffer)
                arr_len = self._current_lengths[-1]
                if arr_len < 0:
                    tmp.len = arr_len
                    _ret.append(tmp)
                    self._parser_states[-1] = ParserState.wait_data
                    return

                self._parser_states.append(ParserState.wait_data)  # 更进一层套娃
                self._current_lengths.append(None)
                for _ in range(arr_len):
                    parse(tmp)
                    if self._parser_states[-1] != ParserState.wait_data:
                        self._buffer = Buffer(buffer_copy)  # 数据不够 直接还原buffer todo 多层呢？
                        del self._parser_states[1:]
                        del self._current_lengths[1:]
                        return

                self._parser_states.pop()
                self._current_lengths.pop()
                self._parser_states[-1] = ParserState.wait_data
                tmp.len = len(tmp)
                _ret.append(tmp)

        ret = []
        while True:  # 多个消息粘包
            before = len(self._buffer)
            parse(ret)
            if len(self._buffer) == before or not self._buffer:
                break

        return ret

    def clear(self):
        self._buffer.clear()

    def send_command(self, *cmd) -> bytes:
        pass


class HiredisConnection(Connection):
    pass
