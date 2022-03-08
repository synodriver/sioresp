from typing import Optional


class Buffer(bytearray):
    def readline(self) -> Optional[bytearray]:
        idx = self.find(b"\r\n")
        if idx == -1:
            return None
        ret = self[:idx]
        del self[: idx + 2]
        return ret

    def read(self, nbytes: int) -> bytearray:
        ret = self[:nbytes]
        del self[:nbytes]
        return ret

    def skip(self, nbytes: int) -> None:
        del self[:nbytes]
