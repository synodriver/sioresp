from typing import Optional


class Buffer(bytearray):
    def readline(self) -> Optional["Buffer"]:
        idx = self.find(b"\r\n")
        if idx == -1:
            return None
        ret = self[:idx]
        del self[: idx + 2]
        return Buffer(ret)

    def read(self, nbytes: int) -> "Buffer":
        ret = self[:nbytes]
        del self[:nbytes]
        return Buffer(ret)

    def skip(self, nbytes: int) -> None:
        del self[:nbytes]
