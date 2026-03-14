"""List commands."""
from collections import deque
from incache.protocol import RESPError, SimpleString


def cmd_lpush(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    d = store.get_or_create_list(key)
    for v in args[1:]:
        d.appendleft(v)
    return len(d)


def cmd_rpush(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    d = store.get_or_create_list(key)
    for v in args[1:]:
        d.append(v)
    return len(d)


def cmd_lpop(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return None
    if entry["type"] != "list":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    d = entry["value"]
    if not d:
        return None
    val = d.popleft()
    store.remove_if_empty(key)
    return val


def cmd_rpop(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return None
    if entry["type"] != "list":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    d = entry["value"]
    if not d:
        return None
    val = d.pop()
    store.remove_if_empty(key)
    return val


def cmd_lrange(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    start = int(args[1])
    stop = int(args[2])
    entry = store.get_entry(key)
    if entry is None:
        return []
    if entry["type"] != "list":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    d = entry["value"]
    length = len(d)
    if start < 0:
        start = max(length + start, 0)
    if stop < 0:
        stop = length + stop
    return list(d)[start:stop + 1]


def cmd_llen(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return 0
    if entry["type"] != "list":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    return len(entry["value"])


def cmd_lindex(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    index = int(args[1])
    entry = store.get_entry(key)
    if entry is None:
        return None
    if entry["type"] != "list":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    d = entry["value"]
    if index < 0:
        index = len(d) + index
    if index < 0 or index >= len(d):
        return None
    return d[index]


def cmd_lset(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    index = int(args[1])
    value = args[2]
    entry = store.get_entry(key)
    if entry is None:
        return RESPError("ERR no such key")
    if entry["type"] != "list":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    d = entry["value"]
    if index < 0:
        index = len(d) + index
    if index < 0 or index >= len(d):
        return RESPError("ERR index out of range")
    d[index] = value
    return SimpleString("OK")


def cmd_linsert(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    where = args[1].upper() if isinstance(args[1], bytes) else args[1].upper()
    if isinstance(where, bytes):
        where = where.decode()
    pivot = args[2]
    value = args[3]
    entry = store.get_entry(key)
    if entry is None:
        return 0
    if entry["type"] != "list":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    d = entry["value"]
    lst = list(d)
    for i, item in enumerate(lst):
        if item == pivot:
            if where == "BEFORE":
                lst.insert(i, value)
            else:
                lst.insert(i + 1, value)
            d.clear()
            d.extend(lst)
            return len(d)
    return -1


def cmd_lrem(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    count = int(args[1])
    value = args[2]
    entry = store.get_entry(key)
    if entry is None:
        return 0
    if entry["type"] != "list":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    d = entry["value"]
    lst = list(d)
    removed = 0
    if count > 0:
        new = []
        for item in lst:
            if item == value and removed < count:
                removed += 1
            else:
                new.append(item)
    elif count < 0:
        new = []
        for item in reversed(lst):
            if item == value and removed < abs(count):
                removed += 1
            else:
                new.append(item)
        new.reverse()
    else:
        new = [item for item in lst if item != value]
        removed = len(lst) - len(new)
    d.clear()
    d.extend(new)
    store.remove_if_empty(key)
    return removed
