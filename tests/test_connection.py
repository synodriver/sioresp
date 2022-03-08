from unittest import TestCase

from sioresp import Connection, Config
from sioresp.events import String, ReplyError, Integer


class TestCon(TestCase):
    def setUp(self) -> None:
        self.con = Connection(Config())

    def test_str(self):
        data = self.con.feed_data(b"+OK\r\n")[0]
        self.assertEqual(str(data), "OK")
        self.assertEqual(type(data), String)
        self.con.clear()

    def test_error(self):
        data = self.con.feed_data(b"-Error message\r\n")[0]
        self.assertEqual(str(data), "Error message")
        self.assertEqual(type(data), ReplyError)
        self.con.clear()

    def test_integer(self):
        data = self.con.feed_data(b":1000\r\n")[0]
        self.assertEqual(int(data), 1000)
        self.assertEqual(type(data), Integer)
        self.con.clear()

    def test_bulkstring(self):
        data = self.con.feed_data(b"$8\r\nfoo\r\nbar\r\n")[0]
        self.assertEqual(str(data), "foo\r\nbar")
        self.assertEqual(type(data), String)
        self.con.clear()

    def test_emptybulkstring(self):
        data = self.con.feed_data(b"$0\r\n\r\n")[0]
        self.assertEqual(str(data), "")
        self.assertEqual(type(data), String)
        self.con.clear()

    def test_nonelbulkstring(self):
        data = self.con.feed_data(b"$-1\r\n")[0]
        self.assertEqual(data, None)
        self.con.clear()

    def test_array(self):
        data = self.con.feed_data(b"*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n")[0]
        data = list(map(lambda x: str(x), data))
        self.assertEqual(data, ["foo", "bar"])
        self.assertEqual(len(self.con._parser_states), 1)
        self.assertEqual(len(self.con._current_lengths), 1)
        self.con.clear()

    def test_emptyarray(self):
        data = self.con.feed_data(b"*0\r\n")[0]
        self.assertEqual(data, [])
        self.assertEqual(len(self.con._parser_states), 1)
        self.assertEqual(len(self.con._current_lengths), 1)

    def test_negaarray(self):
        data = self.con.feed_data(b"*-1\r\n")[0]
        self.assertEqual(data, [])

    def test_arrayarray(self):
        data = self.con.feed_data(b"*2\r\n*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n")[0]
        self.assertEqual(len(data), 2)
        self.assertEqual(len(data[0]), 2)
        self.assertEqual(len(data[1]), 2)
        self.assertEqual(len(self.con._buffer), 0)
        self.assertEqual(len(self.con._parser_states), 1)
        self.assertEqual(len(self.con._current_lengths), 1)
        print(data)

    #  不完整的消息
    def test_unstr(self):
        data = self.con.feed_data(b"+OK")
        self.assertEqual(data, [])
        data = self.con.feed_data(b"\r\n")[0]
        self.assertEqual(str(data), "OK")
        self.assertEqual(type(data), String)
        self.con.clear()

    def test_unbulkstring(self):
        data = self.con.feed_data(b"$8\r\nfoo\r\nbar")
        self.assertEqual(data, [])
        data = self.con.feed_data(b"\r\n")[0]
        self.assertEqual(str(data), "foo\r\nbar")
        self.assertEqual(type(data), String)
        self.con.clear()

    def test_unarray(self):
        self.con.feed_data(b"*2\r\n$3\r\nfoo\r\n$3\r\nbar")
        data = self.con.feed_data(b"\r\n")[0]
        data = list(map(lambda x: str(x), data))
        self.assertEqual(data, ["foo", "bar"])
        self.con.clear()
