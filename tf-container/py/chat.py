import re
from asyncio import run
from typing import NamedTuple


from py.color import color_from_string, colorize
from py.tfutils import TriggerMatching, TriggerPriority, tfprint, trigger
from py.sockets import (
    ChannelMessage,
    Socket,
    TellMessage,
    send_object,
    socket_client,
    socket_server,
)

# /trigger chan_tell: Ruska tells you 'hello'

TELL_RE = re.compile(r"^chan_tell: (.+) tells? (.+) '(.+)'$")
CHANNEL_RE = re.compile(r"^chan_([a-z+-]+): (.+) .[a-z+-]+.: (.+)$")


class State(NamedTuple):
    whoami: str | None
    enabled_channels: list[str] = ["party", "spark+"]


STATE = State("Astrax")


def update_whoami(whoami: str):
    global STATE
    STATE = STATE._replace(whoami=whoami)


def parse_receivers(receivers: str) -> list[str]:
    names_only = re.sub(r"(.+?)(?: \(.+?\))", r"\1", receivers)
    splitted = names_only.split(" and ")
    names = splitted[0].split(", ") + splitted[1:]
    return names


async def sender(message: TellMessage | ChannelMessage):
    async with socket_client(Socket.CHAT) as (_, writer):
        await send_object(writer, message)


def tell_cb(s: str):
    if match := TELL_RE.match(s):
        msg_sender = match.group(1)
        receivers = parse_receivers(match.group(2))
        message = match.group(3)
        msg = TellMessage(msg_sender, receivers, message)
        run(sender(msg))


def channel_cb(s: str):
    if match := CHANNEL_RE.match(s):
        msg_sender = match.group(1)
        channel = match.group(2)
        message = match.group(3)
        if msg_sender == STATE.whoami:
            msg = ChannelMessage("you", channel, message)
        else:
            msg = ChannelMessage(msg_sender, channel, message)

        run(sender(msg))


def init_tf():
    trigger(TELL_RE, "chat.tell_cb", TriggerPriority.BCPROXY_MESSAGE)
    trigger(CHANNEL_RE, "chat.channel_cb", TriggerPriority.BCPROXY_MESSAGE)
    tfprint("Loaded chat")


## server fns


def server_print_tell(msg: TellMessage):
    sender = colorize(msg.sender, color_from_string(msg.sender))
    receivers = ", ".join(
        colorize(r, color_from_string(r)) for r in sorted(msg.receivers)
    )

    if msg.sender == "you" or msg.sender == "You":
        print(f"{receivers} < {msg.message}")
    elif msg.receivers == ["you"] or msg.receivers == ["You"]:
        print(f"{sender} > {msg.message}")
    else:
        print(f"{sender} > {receivers}: {msg.message}")


def server_print_channel(msg: ChannelMessage):
    sender = colorize(msg.sender, color_from_string(msg.sender))
    channel = colorize(msg.channel, color_from_string(msg.channel))

    if msg.sender == "you" or msg.sender == "You":
        print(f"[{channel}] < {msg.message}")
    else:
        print(f"{sender} [{channel}]: {msg.message}")


def receiver(msg: TellMessage | ChannelMessage):
    if isinstance(msg, TellMessage):
        server_print_tell(msg)
    elif isinstance(msg, ChannelMessage):
        server_print_channel(msg)


if __name__ == "__main__":
    run(socket_server(Socket.CHAT, sender, receiver))
else:
    init_tf()
