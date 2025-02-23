import pickle
from asyncio import StreamReader, StreamWriter, open_unix_connection, start_unix_server
from contextlib import asynccontextmanager
from enum import StrEnum
from typing import Any, AsyncIterator, Callable, Coroutine, NamedTuple, TypeVar


class Socket(StrEnum):
    CHAT = "/run/bcproxy-tf/chat.sock"


# Message types have to be defined in this file so that message type checking
# works correctly when they are sent from for example py.chat module
# and received in __init__


class TellMessage(NamedTuple):
    sender: str
    receivers: list[str]
    message: str


class ChannelMessage(NamedTuple):
    sender: str
    channel: str
    message: str


T = TypeVar("T")


async def socket_server(
    socket: Socket,
    _sender: Callable[[T], Coroutine[Any, Any, None]],
    receiver: Callable[[T], None],
):
    async def callback(reader: StreamReader, _: StreamWriter):
        bytes = await reader.read()
        msg = pickle.loads(bytes)
        receiver(msg)

    server = await start_unix_server(callback, socket)

    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()


@asynccontextmanager
async def socket_client(
    socket: Socket,
) -> AsyncIterator[tuple[StreamReader, StreamWriter]]:
    reader, writer = await open_unix_connection(socket)
    try:
        yield reader, writer
    finally:
        writer.close()
        await writer.wait_closed()


async def send_object(writer: StreamWriter, obj: object):
    writer.write(pickle.dumps(obj))
    await writer.drain()
