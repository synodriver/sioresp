from unittest import TestCase

from sioresp import Connection, Config, ParserState
from sioresp.events import String, ReplyError, Integer, need_more_data


class TestCon(TestCase):
    def setUp(self) -> None:
        self.con = Connection(Config())

    def test_str(self):
        self.con.feed_data(b"+OK\r\n")
        data = self.con.next_element()
        self.assertEqual(data, b"OK")
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_error(self):
        self.con.feed_data(b"-Error message\r\n")
        try:
            data = self.con.next_element()
        except Exception as e:
            self.assertEqual(str(e), "Error message")
            self.assertEqual(type(e), ReplyError)
            self.assertEqual(len(self.con._buffer), 0)
            self.assertEqual(len(self.con._events), 0)
            self.assertEqual(len(self.con._events_backup), 0)
            self.assertEqual(self.con._parser_state, ParserState.wait_data)
            self.con.reset()
            self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_integer(self):
        self.con.feed_data(b":1000\r\n")
        data = self.con.next_element()
        self.assertEqual(data, 1000)
        self.assertEqual(type(data), int)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_bulkstring(self):
        self.con.feed_data(b"$8\r\nfoo\r\nbar\r\n")
        data = self.con.next_element()
        self.assertEqual(data, b"foo\r\nbar")
        self.assertEqual(type(data), bytes)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_emptybulkstring(self):
        self.con.feed_data(b"$0\r\n\r\n")
        data = self.con.next_element()
        self.assertEqual(data, b"")
        self.assertEqual(type(data), bytes)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_nonelbulkstring(self):
        self.con.feed_data(b"$-1\r\n")
        data = self.con.next_element()
        self.assertEqual(data, None)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_array(self):
        self.con.feed_data(b"*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n")
        data = self.con.next_element()
        self.assertEqual(data, [b"foo", b"bar"])
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_emptyarray(self):
        self.con.feed_data(b"*0\r\n")
        data = self.con.next_element()
        self.assertEqual(data, [])
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_negaarray(self):
        self.con.feed_data(b"*-1\r\n")
        data = self.con.next_element()
        self.assertEqual(data, None)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)


    def test_arrayarray(self):
        self.con.feed_data(b"*2\r\n*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n")
        data = self.con.next_element()
        self.assertEqual(len(data), 2)
        self.assertEqual(len(data[0]), 2)
        self.assertEqual(len(data[1]), 2)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    #  不完整的消息
    def test_unstr(self):
        self.con.feed_data(b"+OK")
        data = self.con.next_element()
        self.assertEqual(data, need_more_data )
        self.con.feed_data(b"\r\n")
        data = self.con.next_element()
        self.assertEqual(data, b"OK")
        self.assertEqual(type(data), bytes)
        self.con.reset()

    def test_unbulkstring(self):
        self.con.feed_data(b"$8\r\nfoo\r\nbar")
        data = self.con.next_element()
        self.assertEqual(data, need_more_data)
        self.con.feed_data(b"\r\n")
        data = self.con.next_element()
        self.assertEqual(data, b"foo\r\nbar")
        self.assertEqual(type(data), bytes)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_unarray(self):
        self.con.feed_data(b"*2\r\n$3\r\nfoo\r\n$3\r\nbar")
        data = self.con.next_element()
        self.assertEqual(data, need_more_data)
        self.con.feed_data(b"\r\n")
        data = self.con.next_element()
        data = list(map(lambda x: str(x), data))
        self.assertEqual(data, ["foo", "bar"])
        self.con.reset()
