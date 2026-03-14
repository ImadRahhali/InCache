"""String and key commands."""
import time
import fnmatch
from incache.protocol import RESPError, SimpleString


def cmd_set(store, *args):
    if len(args) < 2:
        return RESPError("ERR wrong number of arguments for 'set' command")
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    value = args[1]
    expires_at = None
    nx = xx = False
    i = 2
    while i < len(args):
        opt = args[i].upper() if isinstance(args[i], bytes) else args[i].upper()
        if isinstance(opt, bytes):
            opt = opt.decode()
        if opt == "EX":
            expires_at = time.time() + int(args[i + 1])
            i += 2
        elif opt == "PX":
            expires_at = time.time() + int(args[i + 1]) / 1000.0
            i += 2
        elif opt == "NX":
            nx = True
            i += 1
        elif opt == "XX":
            xx = True
            i += 1
        else:
            i += 1
    if nx and store.exists(key):
        return None
    if xx and not store.exists(key):
        return None
    store.set_value(key, value, "string", expires_at)
    return SimpleString("OK")


def cmd_get(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return None
    if entry["type"] != "string":
        return RESPError("WRONGTYPE Operation against a key holding the wrong kind of value")
    return entry["value"]


def cmd_getset(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    new_value = args[1]
    old = store.get_entry(key)
    old_val = old["value"] if old else None
    store.set_value(key, new_value, "string")
    return old_val


def cmd_mset(store, *args):
    for i in range(0, len(args), 2):
        key = args[i].decode() if isinstance(args[i], bytes) else args[i]
        store.set_value(key, args[i + 1], "string")
    return SimpleString("OK")


def cmd_mget(store, *args):
    result = []
    for a in args:
        key = a.decode() if isinstance(a, bytes) else a
        entry = store.get_entry(key)
        if entry is None or entry["type"] != "string":
            result.append(None)
        else:
            result.append(entry["value"])
    return result


def cmd_del(store, *args):
    count = 0
    for a in args:
        key = a.decode() if isinstance(a, bytes) else a
        if store.delete(key):
            count += 1
    return count


def cmd_exists(store, *args):
    count = 0
    for a in args:
        key = a.decode() if isinstance(a, bytes) else a
        if store.exists(key):
            count += 1
    return count


def _incr_by(store, key_arg, amount):
    key = key_arg.decode() if isinstance(key_arg, bytes) else key_arg
    entry = store.get_entry(key)
    if entry is None:
        store.set_value(key, str(amount).encode(), "string")
        return amount
    if entry["type"] != "string":
        raise Exception("WRONGTYPE Operation against a key holding the wrong kind of value")
    try:
        val = int(entry["value"])
    except (ValueError, TypeError):
        raise Exception("value is not an integer or out of range")
    val += amount
    entry["value"] = str(val).encode()
    return val


def cmd_incr(store, *args):
    return _incr_by(store, args[0], 1)


def cmd_incrby(store, *args):
    amount = int(args[1])
    return _incr_by(store, args[0], amount)


def cmd_decr(store, *args):
    return _incr_by(store, args[0], -1)


def cmd_decrby(store, *args):
    amount = int(args[1])
    return _incr_by(store, args[0], -amount)


def cmd_append(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    value = args[1]
    if isinstance(value, str):
        value = value.encode()
    entry = store.get_entry(key)
    if entry is None:
        store.set_value(key, value, "string")
        return len(value)
    if entry["type"] != "string":
        return RESPError("WRONGTYPE Operation against a key holding the wrong kind of value")
    old = entry["value"]
    if isinstance(old, str):
        old = old.encode()
    new = old + value
    entry["value"] = new
    return len(new)


def cmd_strlen(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    entry = store.get_entry(key)
    if entry is None:
        return 0
    v = entry["value"]
    if isinstance(v, str):
        return len(v)
    return len(v)


def cmd_setnx(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    if store.exists(key):
        return 0
    store.set_value(key, args[1], "string")
    return 1


def cmd_setex(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    seconds = int(args[1])
    value = args[2]
    store.set_value(key, value, "string", time.time() + seconds)
    return SimpleString("OK")


def cmd_expire(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    seconds = int(args[1])
    if store.set_expiry(key, time.time() + seconds):
        return 1
    return 0


def cmd_ttl(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    exp = store.get_expiry(key)
    if exp == -2:
        return -2
    if exp == -1:
        return -1
    remaining = exp - time.time()
    if remaining <= 0:
        return -2
    return int(remaining)


def cmd_persist(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    return 1 if store.persist(key) else 0


def cmd_type(store, *args):
    key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    return SimpleString(store.get_type(key))


def cmd_rename(store, *args):
    old_key = args[0].decode() if isinstance(args[0], bytes) else args[0]
    new_key = args[1].decode() if isinstance(args[1], bytes) else args[1]
    entry = store.get_entry(old_key)
    if entry is None:
        return RESPError("ERR no such key")
    store._data[new_key] = entry
    del store._data[old_key]
    return SimpleString("OK")


def cmd_keys(store, *args):
    pattern = args[0].decode() if isinstance(args[0], bytes) else args[0]
    all_keys = store.keys()
    matched = [k.encode() for k in all_keys if fnmatch.fnmatch(k, pattern)]
    return matched
