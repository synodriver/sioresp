from unittest import TestCase

from sioresp import Connection, Config, ParserState
from sioresp.events import String, ReplyError, Integer
from sioresp.exceptions import ProtocolError


class TestPack(TestCase):
    def setUp(self) -> None:
        self.con = Connection(Config(resp_version=3))

    def test_send(self):
        data = self.con.send_command("GET", "key")
        self.con.feed_data(data)
        data = next(self.con)
        self.assertEqual(data, [b'GET', b'key'])

    def test_map(self):
        data = self.con.send_command({"key": "val"})
        self.con.feed_data(data)
        data = next(self.con)
        self.assertEqual(data, [(b'key', b'val')])

    def test_push(self):
        data = self.con.pack_push([1, 2, 3])
        self.con.feed_data(data)
        data = next(self.con)
        self.assertEqual(data, [1, 2, 3])

    def test_packstring(self):
        data = self.con.pack_string("OK")
        self.assertEqual(data, b"+OK\r\n")

    def test_packbulkstring(self):
        data = self.con.send_command("OK")
        self.con.feed_data(data)
        ok = next(self.con)
        self.assertEqual(ok, b"OK")
