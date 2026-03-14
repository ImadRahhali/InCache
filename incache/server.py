"""TCP server using asyncio."""
import asyncio
from incache.protocol import RESPParser, encode
from incache.store import Store
from incache.commands import dispatch


async def handle_client(reader, writer, store):
    parser = RESPParser()
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            parser.feed(data)
            commands = parser.parse()
            for cmd in commands:
                if not cmd:
                    continue
                if isinstance(cmd, list):
                    cmd_name = cmd[0]
                    if isinstance(cmd_name, bytes):
                        cmd_name = cmd_name.decode()
                    args = cmd[1:]
                else:
                    continue
                result = await dispatch(store, cmd_name, args)
                writer.write(encode(result))
            await writer.drain()
    except (ConnectionResetError, BrokenPipeError, asyncio.CancelledError):
        pass
    finally:
        writer.close()


async def run_server(host="0.0.0.0", port=6399):
    store = Store()
    store.start_expiry_sweep()

    server = await asyncio.start_server(
        lambda r, w: handle_client(r, w, store), host, port
    )
    async with server:
        await server.serve_forever()
