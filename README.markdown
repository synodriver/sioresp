# sioresp

### sans-io风格的redis协议解析器 支持resp2 resp3

# 使用

```python
from sioresp import Connection, Config

c = Connection(Config())
c.feed_data(b"+OK\r\n")
data = next(c) # b"OK"
next(c) # raise StopIteration
c.feed_data(b"~5\r\n+orange\r\n+apple\r\n#t\r\n:100\r\n:999\r\n")
data = next(c)

c.send_command("GET", "key")

```

### TODO

- [x] 反序列化
- [x] 序列化
- [x] 单元测试
- [ ] hiredis加速
- [ ] 文档