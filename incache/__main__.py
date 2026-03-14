"""Entry point: python -m incache"""
import argparse
import asyncio
from incache.server import run_server


def main():
    parser = argparse.ArgumentParser(description="InCache - Redis-compatible in-memory database")
    parser.add_argument("--port", type=int, default=6399)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()
    asyncio.run(run_server(args.host, args.port))


if __name__ == "__main__":
    main()
