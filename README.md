# InCache

A Redis-compatible in-memory database written in pure Python. Speaks the RESP2 protocol — connect with any Redis client, no configuration needed.

```bash
pip install incache
python -m incache       # starts on port 6399
```

```python
import redis
r = redis.Redis(host="localhost", port=6399, decode_responses=True)

r.set("hello", "world", ex=60)
r.get("hello")           # "world"
r.incr("counter")        # 1
r.lpush("queue", "job1")
r.hset("user:1", mapping={"name": "Imad", "role": "engineer"})
r.sadd("tags", "python", "cache", "redis")
```

Built as a learning project to understand how Redis works internally — inspired by the [vinext methodology](https://blog.cloudflare.com/vinext) of using an existing project's own test suite as the implementation spec. The quality gate is 149 pytest tests written against real Redis command behaviour.

---

## Benchmarks

Benchmarked on **Apple M4 Pro**, macOS, 100k operations, 10 parallel clients, using `valkey-benchmark`.

### Simple commands (ops/sec)

| Command | InCache (Python) | Redis 8.6.1 (macOS) | Redis 8.6.1 (Linux)* |
|---------|-----------------|---------------------|----------------------|
| SET     | **57,142**      | 7,184               | ~110,000             |
| GET     | **59,241**      | 3,903               | ~120,000             |
| INCR    | **61,236**      | 4,849               | ~110,000             |
| LPUSH   | **59,808**      | 4,480               | ~110,000             |
| HSET    | **58,139**      | 6,538               | ~105,000             |

*Linux estimates from Redis official benchmarks on comparable hardware.

### LRANGE (ops/sec)

| Elements | InCache (Python) | Redis 8.6.1 (macOS) |
|----------|-----------------|---------------------|
| 100      | **24,038**      | 2,868               |
| 300      | **12,690**      | 5,213               |
| 500      | **8,568**       | 5,393               |
| 600      | **7,342**       | 4,494               |

### Latency (p50 / p99, milliseconds)

| Command | InCache         | Redis 8.6.1 (macOS) |
|---------|-----------------|---------------------|
| SET     | 0.167 / 0.263   | 1.335 / 3.807       |
| GET     | 0.159 / 0.223   | 2.023 / 7.079       |
| INCR    | 0.159 / 0.191   | 1.415 / 6.511       |
| LPUSH   | 0.159 / 0.199   | 1.511 / 6.759       |
| HSET    | 0.167 / 0.207   | 1.335 / 4.775       |

### Why does InCache beat Redis on macOS?

It doesn't — not in any meaningful sense. **On Linux, Redis runs at 100k–120k ops/sec**, roughly 2× InCache. The macOS results are misleading for two reasons:

1. **Redis is optimised for Linux `epoll`**. On macOS it falls back to `kqueue` and performs significantly worse. This is a known, well-documented limitation.
2. **Python `asyncio` happens to handle macOS `kqueue` efficiently** for this specific workload — single process, loopback connections, small fixed payloads.

The honest comparison is InCache Python (~58k ops/sec) vs Redis Linux (~110k ops/sec). Redis is ~2× faster. InCache V2 in Rust is expected to close or exceed that gap — see the roadmap below.

### Run benchmarks yourself

```bash
python -m incache --port 6399 &
valkey-benchmark -p 6399 -t set,get,incr,lpush,hset -n 100000 -c 10
valkey-benchmark -p 6399 -t lrange -n 10000 -c 10
```

---

## Features

**Data structures**

- **Strings** — `SET`, `GET`, `MSET`, `MGET`, `GETSET`, `SETNX`, `SETEX`, `INCR`, `INCRBY`, `DECR`, `DECRBY`, `APPEND`, `STRLEN`
- **Lists** — `LPUSH`, `RPUSH`, `LPOP`, `RPOP`, `LRANGE`, `LLEN`, `LINDEX`, `LSET`, `LINSERT`, `LREM`
- **Hashes** — `HSET`, `HGET`, `HMSET`, `HMGET`, `HGETALL`, `HDEL`, `HEXISTS`, `HLEN`, `HKEYS`, `HVALS`, `HINCRBY`
- **Sets** — `SADD`, `SMEMBERS`, `SREM`, `SISMEMBER`, `SCARD`, `SUNION`, `SINTER`, `SDIFF`, `SMOVE`, `SPOP`

**TTL / expiry**

- `EXPIRE`, `TTL`, `PERSIST`, `SETEX`, `SET EX/PX/NX/XX`
- Lazy expiry — checked on every key access
- Active expiry sweep — background coroutine runs every 100ms

**Key commands** — `TYPE`, `RENAME`, `KEYS` (glob patterns), `EXISTS`, `DEL`

**Server** — `PING`, `ECHO`, `FLUSHALL`, `FLUSHDB`, `DBSIZE`, `INFO`, `SELECT`, `COMMAND COUNT`, `HELLO`

**Protocol** — full RESP2, pipelining, partial frame reads, inline commands

---

## Install

```bash
pip install incache
```

Requires Python 3.11+. Zero runtime dependencies — pure stdlib.

---

## Usage

**Start the server**

```bash
python -m incache                     # default: 0.0.0.0:6399
python -m incache --port 6380         # custom port
incache --port 6399                   # if installed via pip
```

**Connect with any Redis client**

```python
import redis

r = redis.Redis(host="localhost", port=6399, decode_responses=True)

# Strings with TTL
r.set("session:abc", "user:42", ex=3600)
r.ttl("session:abc")   # ~3600

# Atomic counters
r.set("page:views", 0)
r.incrby("page:views", 10)   # 10

# Lists as queues
r.rpush("jobs", "send_email", "resize_image", "send_sms")
r.lpop("jobs")   # "send_email"

# Hashes as records
r.hset("user:1", mapping={"name": "Imad", "plan": "pro", "credits": "100"})
r.hincrby("user:1", "credits", -10)   # 90
r.hgetall("user:1")   # {"name": "Imad", "plan": "pro", "credits": "90"}

# Sets for unique membership
r.sadd("online", "u1", "u2", "u3")
r.sismember("online", "u2")   # 1
r.scard("online")   # 3
```

---

## Architecture

InCache is ~800 lines of pure Python across 8 files.

```
incache/
├── __main__.py      # CLI entrypoint (--host, --port)
├── server.py        # asyncio TCP server — one coroutine per connection
├── protocol.py      # RESP2 parser + serialiser
│                    #   pipelining, partial reads, inline commands
│                    #   SimpleString vs bulk string distinction
├── store.py         # in-memory store with TTL
│                    #   lazy expiry on every key access
│                    #   active sweep coroutine every 100ms
│                    #   asyncio.Lock for concurrent mutation safety
└── commands/
    ├── __init__.py  # command dispatcher — name → handler function
    ├── strings.py   # string + key commands
    ├── lists.py     # list commands (collections.deque for O(1) push/pop)
    │                #   LRANGE uses itertools.islice — O(slice) not O(list)
    ├── hashes.py    # hash commands (dict)
    ├── sets.py      # set commands (set)
    └── server.py    # server commands + HELLO handshake
```

**asyncio throughout.** A single event loop handles all connections. No threads, no GIL contention. Each client connection is a coroutine that reads from a socket buffer, parses RESP frames, dispatches commands, and writes responses.

**`collections.deque` for lists.** O(1) push and pop on both ends. `LRANGE` uses `itertools.islice` to walk only to `start + count` — never materialises the full deque into a list. This was a 15× performance fix: LRANGE 100 went from 1,580 ops/sec to 24,038 ops/sec.

**Lazy + active TTL expiry.** Every key access checks `time.time() > expires_at` (lazy). A background coroutine sweeps the full keyspace every 100ms (active), preventing unbounded memory growth from keys that are never read again.

**`SimpleString` wrapper.** RESP2 distinguishes `+OK\r\n` (simple string) from `$2\r\nOK\r\n` (bulk string). A `SimpleString` dataclass lets command handlers return the right encoding — critical for redis-py's `PING` callback compatibility.

---

## Tests

149 tests across all data types and server commands, written against the real redis-py client. The test suite is the spec — if it passes, the behaviour matches Redis.

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

```
tests/test_strings.py   48 tests — SET/GET flags, TTL, INCR, APPEND, TYPE, KEYS, RENAME
tests/test_lists.py     30 tests — push/pop, LRANGE, LINDEX, LSET, LINSERT, LREM
tests/test_hashes.py    27 tests — HSET, HMGET, HGETALL, HINCRBY, HEXISTS
tests/test_sets.py      31 tests — SADD, set operations, SMOVE, SPOP
tests/test_server.py    13 tests — PING, ECHO, FLUSH, DBSIZE, SELECT, INFO
```

The `conftest.py` fixture auto-starts the server as a subprocess and issues `FLUSHALL` before each test for full isolation.

---

## Roadmap — InCacheV2 (Rust)

InCache V2 will reimplement the same architecture, same RESP2 protocol, and pass the same 149 tests — in Rust.

Planned stack: **Tokio** (async runtime) · **Bytes** crate (zero-copy RESP parsing) · **DashMap** (lock-free concurrent hashmap) · **VecDeque** (O(1) list operations)

Target benchmarks on the same M4 Pro:

| | InCache Python | InCache V2 Rust (target) | Redis Linux |
|---|---|---|---|
| SET | 57,142 | ~300,000 | ~110,000 |
| GET | 59,241 | ~350,000 | ~120,000 |
| LRANGE 100 | 24,038 | ~150,000 | ~80,000 |

The three-way comparison will tell a clean story: Python productivity baseline → Rust systems performance → production C database.

---

## Limitations

InCache is a learning project, not a production database:

- No persistence — data is lost on restart
- No replication, clustering, Lua scripting, sorted sets, streams, or pub/sub
- No authentication, ACLs, or TLS
- Single-threaded — one CPU core only

For production workloads, use [Redis](https://redis.io) or [Valkey](https://valkey.io).

---

## License

MIT — see [LICENSE](LICENSE)
