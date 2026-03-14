"""Hash commands."""
from incache.protocol import RESPError, SimpleString


def cmd_hset(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    h = store.get_or_create_hash(key)
    added = 0
    i = 1
    while i < len(args) - 1:
        field = args[i].decode() if isinstance(args[i], bytes) else args[i]
        value = args[i + 1]
        if field not in h:
            added += 1
        h[field] = value
        i += 2
    return added


def cmd_hget(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    field = args[1].decode() if isinstance(args[1], bytes) else args[1]
    entry = store.get_entry(key)
    if entry is None:
        return None
    if entry["type"] != "hash":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    return entry["value"].get(field)


def cmd_hmset(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    h = store.get_or_create_hash(key)
    i = 1
    while i < len(args) - 1:
        field = args[i].decode() if isinstance(args[i], bytes) else args[i]
        h[field] = args[i + 1]
        i += 2
    return SimpleString("OK")


def cmd_hmget(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    result = []
    for a in args[1:]:
        field = a.decode() if isinstance(a, bytes) else a
        if entry is None or entry["type"] != "hash":
            result.append(None)
        else:
            result.append(entry["value"].get(field))
    return result


def cmd_hgetall(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return []
    if entry["type"] != "hash":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    result = []
    for field, value in entry["value"].items():
        result.append(field.encode())
        result.append(value)
    return result


def cmd_hdel(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return 0
    if entry["type"] != "hash":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    h = entry["value"]
    count = 0
    for a in args[1:]:
        field = a.decode() if isinstance(a, bytes) else a
        if field in h:
            del h[field]
            count += 1
    store.remove_if_empty(key)
    return count


def cmd_hexists(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    field = args[1].decode() if isinstance(args[1], bytes) else args[1]
    entry = store.get_entry(key)
    if entry is None:
        return 0
    if entry["type"] != "hash":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    return 1 if field in entry["value"] else 0


def cmd_hlen(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return 0
    if entry["type"] != "hash":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    return len(entry["value"])


def cmd_hkeys(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return []
    if entry["type"] != "hash":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    return [k.encode() for k in entry["value"].keys()]


def cmd_hvals(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return []
    if entry["type"] != "hash":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    return list(entry["value"].values())


def cmd_hincrby(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    field = args[1].decode() if isinstance(args[1], bytes) else args[1]
    increment = int(args[2])
    h = store.get_or_create_hash(key)
    current = h.get(field)
    if current is None:
        h[field] = str(increment).encode()
        return increment
    try:
        val = int(current)
    except (ValueError, TypeError):
        raise Exception("hash value is not an integer")
    val += increment
    h[field] = str(val).encode()
    return val
