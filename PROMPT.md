# Kiro-CLI Prompt — InCache

Paste this as your first message. Nothing else needed.

---

Read `CLAUDE.md` in full before writing any code.

You are building **InCache** — a Redis-compatible in-memory database in pure Python that speaks the RESP protocol. Real `redis-py` clients must be able to connect and issue commands.

Your quality gate is the test suite in `tests/`. You are done when all tests pass. Do not stop until that happens.

## Workflow
1. Read `CLAUDE.md` completely
2. Read all files in `tests/` to understand exactly what must work
3. Implement following the order in CLAUDE.md under "Implementation Order"
4. After each module passes its tests, make a git commit (messages are listed in CLAUDE.md)
5. When all tests pass, run `pytest tests/ -v`, show me the final summary, then `git push origin main`

## Non-negotiables
- Package name is `incache`, entry point is `python -m incache`
- Use `asyncio` for the TCP server — never block the event loop
- Only stdlib + `redis` (test client only) — no third-party server libraries
- Use `collections.deque` for list values (O(1) push/pop)
- Use Python `set` for set values, `dict` for hash values
- Handle pipelining and partial RESP frames correctly
- Lazy TTL expiry on every key access + active sweep every 100ms

## Git
- Remote is already configured
- Commit after each module passes its tests
- Push to origin main only when ALL tests pass

Start now. Read CLAUDE.md first.
