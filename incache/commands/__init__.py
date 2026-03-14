"""Command dispatcher."""
from incache.store import WrongTypeError
from incache.protocol import RESPError
from incache.commands import server as server_cmds
from incache.commands import strings as string_cmds
from incache.commands import lists as list_cmds
from incache.commands import hashes as hash_cmds
from incache.commands import sets as set_cmds

COMMANDS = {}


def register(name, fn):
    COMMANDS[name.upper()] = fn


# Server commands
register("PING", server_cmds.cmd_ping)
register("ECHO", server_cmds.cmd_echo)
register("FLUSHALL", server_cmds.cmd_flushall)
register("FLUSHDB", server_cmds.cmd_flushdb)
register("DBSIZE", server_cmds.cmd_dbsize)
register("INFO", server_cmds.cmd_info)
register("SELECT", server_cmds.cmd_select)
register("COMMAND", server_cmds.cmd_command)
register("HELLO", server_cmds.cmd_hello)

# String/key commands
register("SET", string_cmds.cmd_set)
register("GET", string_cmds.cmd_get)
register("GETSET", string_cmds.cmd_getset)
register("MSET", string_cmds.cmd_mset)
register("MGET", string_cmds.cmd_mget)
register("DEL", string_cmds.cmd_del)
register("EXISTS", string_cmds.cmd_exists)
register("INCR", string_cmds.cmd_incr)
register("INCRBY", string_cmds.cmd_incrby)
register("DECR", string_cmds.cmd_decr)
register("DECRBY", string_cmds.cmd_decrby)
register("APPEND", string_cmds.cmd_append)
register("STRLEN", string_cmds.cmd_strlen)
register("SETNX", string_cmds.cmd_setnx)
register("SETEX", string_cmds.cmd_setex)
register("EXPIRE", string_cmds.cmd_expire)
register("TTL", string_cmds.cmd_ttl)
register("PERSIST", string_cmds.cmd_persist)
register("TYPE", string_cmds.cmd_type)
register("RENAME", string_cmds.cmd_rename)
register("KEYS", string_cmds.cmd_keys)

# List commands
register("LPUSH", list_cmds.cmd_lpush)
register("RPUSH", list_cmds.cmd_rpush)
register("LPOP", list_cmds.cmd_lpop)
register("RPOP", list_cmds.cmd_rpop)
register("LRANGE", list_cmds.cmd_lrange)
register("LLEN", list_cmds.cmd_llen)
register("LINDEX", list_cmds.cmd_lindex)
register("LSET", list_cmds.cmd_lset)
register("LINSERT", list_cmds.cmd_linsert)
register("LREM", list_cmds.cmd_lrem)

# Hash commands
register("HSET", hash_cmds.cmd_hset)
register("HGET", hash_cmds.cmd_hget)
register("HMSET", hash_cmds.cmd_hmset)
register("HMGET", hash_cmds.cmd_hmget)
register("HGETALL", hash_cmds.cmd_hgetall)
register("HDEL", hash_cmds.cmd_hdel)
register("HEXISTS", hash_cmds.cmd_hexists)
register("HLEN", hash_cmds.cmd_hlen)
register("HKEYS", hash_cmds.cmd_hkeys)
register("HVALS", hash_cmds.cmd_hvals)
register("HINCRBY", hash_cmds.cmd_hincrby)

# Set commands
register("SADD", set_cmds.cmd_sadd)
register("SMEMBERS", set_cmds.cmd_smembers)
register("SREM", set_cmds.cmd_srem)
register("SISMEMBER", set_cmds.cmd_sismember)
register("SCARD", set_cmds.cmd_scard)
register("SUNION", set_cmds.cmd_sunion)
register("SINTER", set_cmds.cmd_sinter)
register("SDIFF", set_cmds.cmd_sdiff)
register("SMOVE", set_cmds.cmd_smove)
register("SPOP", set_cmds.cmd_spop)


async def dispatch(store, cmd_name: str, args: list):
    name = cmd_name.upper()
    handler = COMMANDS.get(name)
    if handler is None:
        return RESPError(f"ERR unknown command '{cmd_name.decode() if isinstance(cmd_name, bytes) else cmd_name}'")
    try:
        return handler(store, *args)
    except WrongTypeError:
        return RESPError("WRONGTYPE Operation against a key holding the wrong kind of value")
    except Exception as e:
        return RESPError(f"ERR {e}")
