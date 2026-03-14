"""Set commands."""


def cmd_sadd(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    s = store.get_or_create_set(key)
    added = 0
    for a in args[1:]:
        v = a.decode() if isinstance(a, bytes) else a
        if v not in s:
            s.add(v)
            added += 1
    return added


def cmd_smembers(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return []
    if entry["type"] != "set":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    return [v.encode() for v in entry["value"]]


def cmd_srem(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return 0
    if entry["type"] != "set":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    s = entry["value"]
    count = 0
    for a in args[1:]:
        v = a.decode() if isinstance(a, bytes) else a
        if v in s:
            s.discard(v)
            count += 1
    store.remove_if_empty(key)
    return count


def cmd_sismember(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    member = args[1].decode() if isinstance(args[1], bytes) else args[1]
    entry = store.get_entry(key)
    if entry is None:
        return 0
    if entry["type"] != "set":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    return 1 if member in entry["value"] else 0


def cmd_scard(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return 0
    if entry["type"] != "set":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    return len(entry["value"])


def _get_set_members(store, key):
    entry = store.get_entry(key)
    if entry is None:
        return set()
    if entry["type"] != "set":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    return entry["value"]


def cmd_sunion(store, *args):
    result = set()
    for a in args:
        key = a.decode() if isinstance(a, bytes) else a
        result |= _get_set_members(store, key)
    return [v.encode() for v in result]


def cmd_sinter(store, *args):
    keys = [a.decode() if isinstance(a, bytes) else a for a in args]
    result = None
    for key in keys:
        members = _get_set_members(store, key)
        if result is None:
            result = set(members)
        else:
            result &= members
    return [v.encode() for v in (result or set())]


def cmd_sdiff(store, *args):
    keys = [a.decode() if isinstance(a, bytes) else a for a in args]
    result = None
    for key in keys:
        members = _get_set_members(store, key)
        if result is None:
            result = set(members)
        else:
            result -= members
    return [v.encode() for v in (result or set())]


def cmd_smove(store, *args):
    src_key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    dst_key = args[1].decode() if isinstance(args[1], bytes) else args[1]
    member = args[2].decode() if isinstance(args[2], bytes) else args[2]
    src_entry = store.get_entry(src_key)
    if src_entry is None:
        return 0
    if src_entry["type"] != "set":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    src = src_entry["value"]
    if member not in src:
        return 0
    src.discard(member)
    store.remove_if_empty(src_key)
    dst = store.get_or_create_set(dst_key)
    dst.add(member)
    return 1


def cmd_spop(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return None
    if entry["type"] != "set":
        from incache.store import WrongTypeError
        raise WrongTypeError()
    s = entry["value"]
    if not s:
        return None
    val = s.pop()
    store.remove_if_empty(key)
    return val.encode()
