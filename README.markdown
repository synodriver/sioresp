# sioresp

### sans-io style redis protocol parser for respv2 and v3

# usage

```python
from sioresp import Connection, Config

c = Connection(Config(resp_version=3))
c.feed_data(b"+OK\r\n")
data = next(c)  # b"OK"
assert data == b"OK"
try:
    next(c)  # raise StopIteration
except Exception as e:
    assert type(e) == StopIteration
c.feed_data(b"~5\r\n+orange\r\n+apple\r\n#t\r\n:100\r\n:999\r\n")
data = next(c)
assert data == {True, 100, 999, b'apple', b'orange'}

data = c.send_command("GET", "key")
assert data == b'*2\r\n$3\r\nGET\r\n$3\r\nkey\r\n'
```

#### Note:

- You can subclass Connection class to rewrite pack_element method to have customs serialize strategies.

### TODO

- [x] deserialize
- [x] serialize
- [x] unitest
- [ ] hiredis parser
- [ ] docs