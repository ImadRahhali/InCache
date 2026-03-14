"""Server commands: PING, ECHO, FLUSHALL, FLUSHDB, DBSIZE, INFO, SELECT, COMMAND."""
from incache.protocol import SimpleString, RESPError


def cmd_hello(store, *args):
    return [
        b"server", b"incache",
        b"version", b"0.1.0",
        b"proto", 2,
        b"id", 1,
        b"mode", b"standalone",
        b"role", b"master",
        b"modules", []
    ]


def cmd_ping(store, *args):
    if args:
        return args[0]
    return SimpleString("PONG")


def cmd_echo(store, *args):
    if not args:
        from incache.protocol import RESPError
        return RESPError("ERR wrong number of arguments for 'echo' command")
    return args[0]


def cmd_flushall(store, *args):
    store.flush()
    return SimpleString("OK")


def cmd_flushdb(store, *args):
    store.flush()
    return SimpleString("OK")


def cmd_dbsize(store, *args):
    return store.dbsize()


def cmd_info(store, *args):
    info = (
        "# Server\r\n"
        "redis_version:0.1.0 (pyredis/InCache)\r\n"
        "tcp_port:6399\r\n"
    )
    return info.encode()


def cmd_select(store, *args):
    if not args:
        from incache.protocol import RESPError
        return RESPError("ERR wrong number of arguments for 'select' command")
    db = args[0]
    if isinstance(db, bytes):
        db = db.decode()
    if db != "0":
        from incache.protocol import RESPError
        return RESPError("ERR DB index is out of range")
    return SimpleString("OK")


def cmd_command(store, *args):
    from incache.commands import COMMANDS
    if args and isinstance(args[0], bytes) and args[0].upper() == b"COUNT":
        return len(COMMANDS)
    return len(COMMANDS)
