from unittest import TestCase

from sioresp import Connection, Config, ParserState
from sioresp.events import String, ReplyError, Integer
from sioresp.exceptions import ProtocolError


class TestParse(TestCase):
    def setUp(self) -> None:
        self.con = Connection(Config())

    def test_str(self):
        self.con.feed_data(b"+OK\r\n")
        data = self.con.__next__()
        self.assertEqual(data, b"OK")
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_error(self):
        self.con.feed_data(b"-Error message\r\n")
        e = self.con.__next__()
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
        data = self.con.__next__()
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
        data = self.con.__next__()
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
        data = self.con.__next__()
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
        data = self.con.__next__()
        self.assertEqual(data, None)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_array(self):
        self.con.feed_data(b"*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n")
        data = self.con.__next__()
        self.assertEqual(data, [b"foo", b"bar"])
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_emptyarray(self):
        self.con.feed_data(b"*0\r\n")
        data = self.con.__next__()
        self.assertEqual(data, [])
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_negaarray(self):
        self.con.feed_data(b"*-1\r\n")
        data = self.con.__next__()
        self.assertEqual(data, None)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_arrayarray(self):
        self.con.feed_data(b"*2\r\n*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n")
        data = self.con.__next__()
        self.assertEqual(len(data), 2)
        self.assertEqual(len(data[0]), 2)
        self.assertEqual(len(data[1]), 2)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_double(self):
        self.con.feed_data(b",1.23\r\n")
        data = next(self.con)
        self.assertEqual(data, 1.23)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_bool(self):
        self.con.feed_data(b"#t\r\n")
        data = next(self.con)
        self.assertEqual(data, True)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

        self.con.feed_data(b"#f\r\n")
        data = next(self.con)
        self.assertEqual(data, False)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_null(self):
        self.con.feed_data(b"_\r\n")
        data = next(self.con)
        self.assertEqual(data, None)
        with self.assertRaises(ProtocolError):
            self.con.feed_data(b"__\r\n")
            data = next(self.con)
            self.con.reset()
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_bignumber(self):
        self.con.feed_data(b"(3492890328409238509324850943850943825024385\r\n")
        data = next(self.con)
        self.assertEqual(data, 3492890328409238509324850943850943825024385)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_map(self):
        self.con.feed_data(b"%2\r\n+first\r\n:1\r\n+second\r\n:2\r\n")
        data = next(self.con)
        self.assertEqual(len(data), 2)
        self.assertEqual(len(data[0]), 2)
        self.assertEqual(len(data[1]), 2)
        self.assertEqual(data[0][0], b'first')

        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_set(self):
        self.con.feed_data(b"~5\r\n+orange\r\n+apple\r\n#t\r\n:100\r\n:999\r\n")
        data = next(self.con)
        self.assertEqual(len(data), 5)
        self.assertIn(True, data)
        self.assertIn(100, data)
        self.assertIn(999, data)
        self.assertIn(b"orange", data)
        self.assertIn(b"apple", data)

        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_emptybyte(self):
        with self.assertRaises(ProtocolError):
            self.con.feed_data(b"|1\r\n +key-popularity\r\n%2\r\n$1\r\na\r\n,0.1923\r\n$1\r\nb\r\n,0.0012\r\n")
            data = next(self.con)

    def test_attr(self):
        self.con.feed_data(b"|1\r\n+key-popularity\r\n%2\r\n$1\r\na\r\n,0.1923\r\n$1\r\nb\r\n,0.0012\r\n")
        data = next(self.con)
        self.assertEqual(len(data), 1)
        self.assertEqual(len(data[0][1]), 2)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_push(self):
        self.con.feed_data(b">4\r\n+pubsub\r\n+message\r\n+somechannel\r\n+this is the message\r\n")
        data = next(self.con)
        self.assertEqual(len(data), 4)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    #  不完整的消息
    def test_unstr(self):
        self.con.feed_data(b"+OK")
        with self.assertRaises(StopIteration):
            next(self.con)
        self.con.feed_data(b"\r\n")
        data = self.con.__next__()
        self.assertEqual(data, b"OK")
        self.assertEqual(type(data), bytes)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_unbulkstring(self):
        self.con.feed_data(b"$8\r\nfoo\r\nbar")
        with self.assertRaises(StopIteration):
            next(self.con)
        self.con.feed_data(b"\r\n")
        data = self.con.__next__()
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
        with self.assertRaises(StopIteration):
            next(self.con)
        self.con.feed_data(b"\r\n")
        data = self.con.__next__()
        self.assertEqual(data, [b"foo", b"bar"])
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_complex(self):
        self.con.feed_data(b"*5\r\n:1\r\n:2\r\n:3\r\n:4\r\n$6\r\nfoobar\r\n")
        data = next(self.con)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)

    def test_split(self):
        self.con.feed_data(b"*5\r\n:1\r")
        with self.assertRaises(StopIteration):
            next(self.con)
        self.con.feed_data(b"\n:2\r\n:3\r\n:4")
        with self.assertRaises(StopIteration):
            next(self.con)
        self.con.feed_data(b"\r\n$6\r\nfoobar\r\n")
        data = next(self.con)
        self.assertEqual(len(data), 5)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._events), 0)
        self.assertEqual(len(self.con._events_backup), 0)
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
        self.con.reset()
        self.assertEqual(self.con._parser_state, ParserState.wait_data)
