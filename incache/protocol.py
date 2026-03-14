"""RESP protocol parser and serialiser."""


class RESPParser:
    def __init__(self):
        self._buf = b""

    def feed(self, data: bytes):
        self._buf += data

    def parse(self) -> list:
        """Extract all complete RESP commands from buffer."""
        results = []
        while self._buf:
            result, consumed = self._parse_one(self._buf)
            if result is None:
                break
            results.append(result)
            self._buf = self._buf[consumed:]
        return results

    def _parse_one(self, buf: bytes):
        """Parse one RESP value. Returns (value, bytes_consumed) or (None, 0)."""
        if not buf:
            return None, 0

        # Inline command (no RESP prefix)
        if buf[0:1] not in (b"+", b"-", b":", b"$", b"*"):
            idx = buf.find(b"\r\n")
            if idx == -1:
                return None, 0
            line = buf[:idx].decode()
            parts = line.split()
            return [p.encode() for p in parts], idx + 2

        idx = buf.find(b"\r\n")
        if idx == -1:
            return None, 0

        prefix = buf[0:1]
        line = buf[1:idx]

        if prefix == b"+":
            return buf[1:idx], idx + 2
        if prefix == b"-":
            return buf[1:idx], idx + 2
        if prefix == b":":
            return int(line), idx + 2
        if prefix == b"$":
            length = int(line)
            if length == -1:
                return None, idx + 2
            end = idx + 2 + length + 2
            if len(buf) < end:
                return None, 0
            return buf[idx + 2 : idx + 2 + length], end
        if prefix == b"*":
            count = int(line)
            if count == -1:
                return None, idx + 2
            pos = idx + 2
            items = []
            for _ in range(count):
                item, consumed = self._parse_one(buf[pos:])
                if item is None and consumed == 0:
                    return None, 0
                items.append(item)
                pos += consumed
            return items, pos

        return None, 0


def encode(value) -> bytes:
    """Encode a Python value into RESP bytes."""
    if value is None:
        return b"$-1\r\n"
    if isinstance(value, bool):
        return encode(1 if value else 0)
    if isinstance(value, int):
        return f":{value}\r\n".encode()
    if isinstance(value, SimpleString):
        return f"+{value.value}\r\n".encode()
    if isinstance(value, str):
        encoded = value.encode()
        return b"$" + str(len(encoded)).encode() + b"\r\n" + encoded + b"\r\n"
    if isinstance(value, bytes):
        return b"$" + str(len(value)).encode() + b"\r\n" + value + b"\r\n"
    if isinstance(value, list):
        parts = [f"*{len(value)}\r\n".encode()]
        for item in value:
            parts.append(encode(item))
        return b"".join(parts)
    if isinstance(value, RESPError):
        return f"-{value.message}\r\n".encode()
    return encode(str(value))


class SimpleString:
    def __init__(self, value: str):
        self.value = value


class RESPError:
    def __init__(self, message: str):
        self.message = message
