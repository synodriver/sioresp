# sioresp

### sans-io风格的redis协议解析器 支持resp2 resp3

# 使用

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

### TODO

- [x] 反序列化
- [x] 序列化
- [x] 单元测试
- [ ] hiredis加速
- [ ] 文档