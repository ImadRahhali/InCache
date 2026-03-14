"""In-memory data store with TTL expiry."""
import asyncio
import time
from collections import deque


class Store:
    def __init__(self):
        self._data: dict = {}
        self._lock = asyncio.Lock()
        self._sweep_task = None

    def start_expiry_sweep(self):
        self._sweep_task = asyncio.create_task(self._sweep_loop())

    async def _sweep_loop(self):
        while True:
            await asyncio.sleep(0.1)
            now = time.time()
            async with self._lock:
                expired = [
                    k for k, v in self._data.items()
                    if v["expires_at"] is not None and v["expires_at"] <= now
                ]
                for k in expired:
                    del self._data[k]

    def _is_expired(self, key: str) -> bool:
        entry = self._data.get(key)
        if entry and entry["expires_at"] is not None and entry["expires_at"] <= time.time():
            del self._data[key]
            return True
        return False

    def get_entry(self, key: str):
        self._is_expired(key)
        return self._data.get(key)

    def get_value(self, key: str, expected_type: str = None):
        entry = self.get_entry(key)
        if entry is None:
            return None
        if expected_type and entry["type"] != expected_type:
            raise WrongTypeError()
        return entry["value"]

    def set_value(self, key: str, value, vtype: str, expires_at=None):
        self._data[key] = {"type": vtype, "value": value, "expires_at": expires_at}

    def delete(self, key: str) -> bool:
        self._is_expired(key)
        return self._data.pop(key, None) is not None

    def exists(self, key: str) -> bool:
        self._is_expired(key)
        return key in self._data

    def keys(self):
        now = time.time()
        expired = [
            k for k, v in self._data.items()
            if v["expires_at"] is not None and v["expires_at"] <= now
        ]
        for k in expired:
            del self._data[k]
        return list(self._data.keys())

    def flush(self):
        self._data.clear()

    def dbsize(self) -> int:
        now = time.time()
        expired = [
            k for k, v in self._data.items()
            if v["expires_at"] is not None and v["expires_at"] <= now
        ]
        for k in expired:
            del self._data[k]
        return len(self._data)

    def set_expiry(self, key: str, expires_at: float) -> bool:
        entry = self.get_entry(key)
        if entry is None:
            return False
        entry["expires_at"] = expires_at
        return True

    def get_expiry(self, key: str):
        entry = self.get_entry(key)
        if entry is None:
            return -2
        if entry["expires_at"] is None:
            return -1
        return entry["expires_at"]

    def persist(self, key: str) -> bool:
        entry = self.get_entry(key)
        if entry is None or entry["expires_at"] is None:
            return False
        entry["expires_at"] = None
        return True

    def get_type(self, key: str) -> str:
        entry = self.get_entry(key)
        if entry is None:
            return "none"
        return entry["type"]

    def get_or_create_list(self, key: str) -> deque:
        entry = self.get_entry(key)
        if entry is None:
            d = deque()
            self.set_value(key, d, "list")
            return d
        if entry["type"] != "list":
            raise WrongTypeError()
        return entry["value"]

    def get_or_create_hash(self, key: str) -> dict:
        entry = self.get_entry(key)
        if entry is None:
            h = {}
            self.set_value(key, h, "hash")
            return h
        if entry["type"] != "hash":
            raise WrongTypeError()
        return entry["value"]

    def get_or_create_set(self, key: str) -> set:
        entry = self.get_entry(key)
        if entry is None:
            s = set()
            self.set_value(key, s, "set")
            return s
        if entry["type"] != "set":
            raise WrongTypeError()
        return entry["value"]

    def remove_if_empty(self, key: str):
        entry = self._data.get(key)
        if entry and len(entry["value"]) == 0:
            del self._data[key]


class WrongTypeError(Exception):
    pass
