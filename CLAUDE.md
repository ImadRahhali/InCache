# InCache — Build Spec for AI

You are building **InCache**: a Redis-compatible in-memory database written in pure Python.
It must speak the real Redis RESP protocol so any `redis-py` client can connect to it.

---

## ⚠️ Rules

- Do NOT stop until every test in `tests/` passes.
- Do NOT ask clarifying questions. Make decisions and implement.
- Read this entire file before writing a single line of code.
- The test suite is the single source of truth. If a test fails, fix your implementation.
- After every file you create, run `pytest tests/ -x --tb=short` and fix failures before moving on.

---

## Project Structure

```
InCache/
├── incache/
│   ├── __init__.py
│   ├── __main__.py          # Entry point: python -m incache
│   ├── server.py            # TCP server, accept connections, spawn handlers
│   ├── protocol.py          # RESP parser + serialiser
│   ├── store.py             # In-memory data store with TTL
│   ├── commands/
│   │   ├── __init__.py      # Command dispatcher
│   │   ├── strings.py       # String commands
│   │   ├── lists.py         # List commands
│   │   ├── hashes.py        # Hash commands
│   │   ├── sets.py          # Set commands
│   │   └── server.py        # Server commands (PING, FLUSHALL, etc.)
├── tests/
│   ├── conftest.py
│   ├── test_strings.py
│   ├── test_lists.py
│   ├── test_hashes.py
│   ├── test_sets.py
│   └── test_server.py
├── pyproject.toml
└── CLAUDE.md
```

---

## Architecture

### 1. TCP Server (`server.py`)
- Listen on `0.0.0.0:6399` by default (configurable via `--port`)
- Use `asyncio` — one coroutine per connection
- Each connection gets its own buffer; parse RESP frames as they arrive
- Pass parsed commands to the dispatcher; write the response back

### 2. RESP Protocol (`protocol.py`)
Redis uses the **RESP (REdis Serialisation Protocol)**. You must implement both directions.

**Types:**
| Symbol | Type | Example |
|--------|------|---------|
| `+` | Simple string | `+OK\r\n` |
| `-` | Error | `-ERR unknown command\r\n` |
| `:` | Integer | `:42\r\n` |
| `$` | Bulk string | `$5\r\nhello\r\n` |
| `*` | Array | `*2\r\n$3\r\nfoo\r\n$3\r\nbar\r\n` |

Null bulk string: `$-1\r\n`
Null array: `*-1\r\n`

Parser must handle:
- Pipelining (multiple commands in one read)
- Partial reads (buffer incomplete frames)
- Inline commands (plain text like `PING\r\n`)

### 3. Data Store (`store.py`)
- Single `Store` class, shared across all connections (use `asyncio.Lock` for mutations)
- Internal dict: `{ key: { "type": str, "value": Any, "expires_at": float | None } }`
- Types: `"string"`, `"list"`, `"hash"`, `"set"`
- TTL: store absolute expiry timestamp (`time.time() + seconds`)
- Lazy expiry: check on every key access, delete if expired
- Active expiry: background task runs every 100ms, sweeps expired keys

### 4. Command Dispatcher (`commands/__init__.py`)
- Map command name (uppercased) → handler function
- Each handler receives `(store: Store, *args: bytes) -> Any`
- Return value is serialised by the protocol layer
- Unknown command → `-ERR unknown command 'xyz'\r\n`
- Wrong arity → `-ERR wrong number of arguments for 'xyz' command\r\n`

---

## Commands to Implement

### String Commands
| Command | Signature | Returns |
|---------|-----------|---------|
| `SET` | `SET key value [EX seconds] [PX ms] [NX\|XX]` | `+OK` or `$-1` (nil) |
| `GET` | `GET key` | Bulk string or nil |
| `GETSET` | `GETSET key value` | Old value or nil |
| `MSET` | `MSET key value [key value ...]` | `+OK` |
| `MGET` | `MGET key [key ...]` | Array of bulk strings |
| `DEL` | `DEL key [key ...]` | Integer (count deleted) |
| `EXISTS` | `EXISTS key [key ...]` | Integer (count existing) |
| `INCR` | `INCR key` | Integer |
| `INCRBY` | `INCRBY key increment` | Integer |
| `DECR` | `DECR key` | Integer |
| `DECRBY` | `DECRBY key decrement` | Integer |
| `APPEND` | `APPEND key value` | Integer (new length) |
| `STRLEN` | `STRLEN key` | Integer |
| `SETNX` | `SETNX key value` | Integer 1 or 0 |
| `SETEX` | `SETEX key seconds value` | `+OK` |

### Key Commands
| Command | Signature | Returns |
|---------|-----------|---------|
| `EXPIRE` | `EXPIRE key seconds` | Integer 1 or 0 |
| `TTL` | `TTL key` | Integer (-1 no expiry, -2 not exists) |
| `PERSIST` | `PERSIST key` | Integer 1 or 0 |
| `TYPE` | `TYPE key` | Simple string |
| `RENAME` | `RENAME key newkey` | `+OK` |
| `KEYS` | `KEYS pattern` | Array (supports `*` glob) |

### List Commands
| Command | Signature | Returns |
|---------|-----------|---------|
| `LPUSH` | `LPUSH key value [value ...]` | Integer (new length) |
| `RPUSH` | `RPUSH key value [value ...]` | Integer (new length) |
| `LPOP` | `LPOP key` | Bulk string or nil |
| `RPOP` | `RPOP key` | Bulk string or nil |
| `LRANGE` | `LRANGE key start stop` | Array |
| `LLEN` | `LLEN key` | Integer |
| `LINDEX` | `LINDEX key index` | Bulk string or nil |
| `LSET` | `LSET key index value` | `+OK` |
| `LINSERT` | `LINSERT key BEFORE\|AFTER pivot value` | Integer |
| `LREM` | `LREM key count value` | Integer (removed count) |

### Hash Commands
| Command | Signature | Returns |
|---------|-----------|---------|
| `HSET` | `HSET key field value [field value ...]` | Integer (new fields added) |
| `HGET` | `HGET key field` | Bulk string or nil |
| `HMSET` | `HMSET key field value [field value ...]` | `+OK` |
| `HMGET` | `HMGET key field [field ...]` | Array |
| `HGETALL` | `HGETALL key` | Array (field, value, field, value...) |
| `HDEL` | `HDEL key field [field ...]` | Integer |
| `HEXISTS` | `HEXISTS key field` | Integer 1 or 0 |
| `HLEN` | `HLEN key` | Integer |
| `HKEYS` | `HKEYS key` | Array |
| `HVALS` | `HVALS key` | Array |
| `HINCRBY` | `HINCRBY key field increment` | Integer |

### Set Commands
| Command | Signature | Returns |
|---------|-----------|---------|
| `SADD` | `SADD key member [member ...]` | Integer (added count) |
| `SMEMBERS` | `SMEMBERS key` | Array |
| `SREM` | `SREM key member [member ...]` | Integer |
| `SISMEMBER` | `SISMEMBER key member` | Integer 1 or 0 |
| `SCARD` | `SCARD key` | Integer |
| `SUNION` | `SUNION key [key ...]` | Array |
| `SINTER` | `SINTER key [key ...]` | Array |
| `SDIFF` | `SDIFF key [key ...]` | Array |
| `SMOVE` | `SMOVE source dest member` | Integer 1 or 0 |
| `SPOP` | `SPOP key` | Bulk string or nil |

### Server Commands
| Command | Returns |
|---------|---------|
| `PING [message]` | `+PONG` or bulk string echo |
| `ECHO message` | Bulk string |
| `FLUSHALL` | `+OK` |
| `FLUSHDB` | `+OK` |
| `DBSIZE` | Integer |
| `INFO` | Bulk string (basic server info) |
| `SELECT db` | `+OK` (support 0 only, others return error) |
| `COMMAND COUNT` | Integer |

---

## Error Handling

- Wrong type operation: `-WRONGTYPE Operation against a key holding the wrong kind of value\r\n`
- Out of range integer: `-ERR value is not an integer or out of range\r\n`
- Index out of range: `-ERR index out of range\r\n`
- Non-existent key for commands that require it: return nil or 0 per Redis behaviour

---

## Implementation Order

Follow this exact order. Run tests after each step.

1. `protocol.py` — RESP parser + serialiser + unit test manually
2. `store.py` — Store class with TTL, lazy + active expiry
3. `server.py` + `commands/__init__.py` — TCP server + dispatcher skeleton
4. `commands/server.py` — PING, ECHO, FLUSHALL, DBSIZE (run `test_server.py`)
5. `commands/strings.py` — all string + key commands (run `test_strings.py`)
6. `commands/lists.py` (run `test_lists.py`)
7. `commands/hashes.py` (run `test_hashes.py`)
8. `commands/sets.py` (run `test_sets.py`)
9. Full `pytest tests/` — fix any remaining failures

## Git Commits

After each step above passes its tests, make a git commit with a conventional commit message:
- `feat: implement RESP protocol parser and serialiser`
- `feat: implement in-memory store with TTL expiry`
- `feat: implement TCP server and command dispatcher`
- `feat: implement server commands (PING, ECHO, FLUSH, DBSIZE)`
- `feat: implement string and key commands`
- `feat: implement list commands`
- `feat: implement hash commands`
- `feat: implement set commands`
- `feat: all tests passing - InCache complete`

When all tests pass, run `git push origin main`.

---

## Performance Goals

- Handle 10,000+ commands/second on a single core
- Use `asyncio` properly — never block the event loop
- Store list values as `collections.deque` for O(1) push/pop
- Store set values as Python `set`
- Store hash values as Python `dict`

---

## Dependencies

Only these are allowed:
- `asyncio` (stdlib)
- `redis` (for tests only — `redis-py` client)
- `pytest`, `pytest-asyncio` (for tests only)

No third-party server libraries. Pure Python.

---

## Running

```bash
# Start server
python -m incache

# Run tests (server must be running)
pytest tests/ -v

# Or use the fixture which auto-starts it
pytest tests/ -v --tb=short
```
