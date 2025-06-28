import re
from asyncio import run


from py.color import color_from_string, colorize
from py.global_state import GLOBAL_STATE
from py.tfutils import TriggerPriority, tfprint, trigger
from py.sockets import (
    ChannelMessage,
    Socket,
    TellMessage,
    send_object,
    socket_client,
    socket_server,
)

"""
chat.py

This module is used for chat-window.

Tells and specified channels are printed to a separate window with modified
colors and formatting.

Tells are sent always, channels must be added separately with:

    /python_call py.chat.add_channel party smoke+

Last messages from channels can also be sent to the chat window with the following
commands:

    command last_tell prefix "chan_tell: " last tell
    command last_smoke prefix "chan_smoke+: " last smoke+

Say-channel and special cases in tell-channel (accepting raises etc.) don't
work correctly.
"""


TELL_RE = re.compile(r"^chan_tell: (?:\(\d\d:\d\d\) )?(.+?) tells? (.+?) '(.+)'$")
CHANNEL_RE = re.compile(
    r"^chan_([a-z+-]+): (?:\[\d\d:\d\d\]:)?(.+?) .[a-z+-]+?.: (.+)$"
)

# channels which are printed to separate window
STATE: set[str] = set()


def add_channel(s: str) -> None:
    global STATE
    channels = s.split(" ")
    for channel in channels:
        STATE.add(channel)


def parse_receivers(receivers: str) -> list[str]:
    names_only = re.sub(r"(.+?)(?: \(.+?\))", r"\1", receivers)
    splitted = names_only.split(" and ")
    names = splitted[0].split(", ") + splitted[1:]
    return names


async def sender(msg: TellMessage | ChannelMessage):
    async with socket_client(Socket.CHAT) as (_, writer):
        await send_object(writer, msg)


def tell_cb(s: str):
    if match := TELL_RE.match(s):
        msg_sender = match.group(1)
        receivers = parse_receivers(match.group(2))
        message = match.group(3)
        msg = TellMessage(msg_sender, receivers, message)
        run(sender(msg))


def channel_cb(s: str):
    if match := CHANNEL_RE.match(s):
        channel = match.group(1)
        msg_sender = match.group(2)
        message = match.group(3)

        if channel not in STATE:
            return

        if msg_sender == GLOBAL_STATE.char_name:
            msg = ChannelMessage("you", channel, message)
        else:
            msg = ChannelMessage(msg_sender, channel, message)

        run(sender(msg))


def init_tf():
    trigger(TELL_RE, tell_cb, TriggerPriority.BCPROXY)
    trigger(CHANNEL_RE, channel_cb, TriggerPriority.BCPROXY)
    tfprint("Loaded chat")


## server fns


def server_print_tell(msg: TellMessage):
    sender = colorize(msg.sender, color_from_string(msg.sender))
    receivers = ", ".join(
        colorize(r, color_from_string(r)) for r in sorted(msg.receivers)
    )

    if msg.sender == "you" or msg.sender == "You":
        print(f"> {receivers} {msg.message}")
    elif msg.receivers == ["you"] or msg.receivers == ["You"]:
        print(f"{sender} > {msg.message}")
    else:
        print(f"{sender} > {receivers}: {msg.message}")


def server_print_channel(msg: ChannelMessage):
    sender = colorize(msg.sender, color_from_string(msg.sender))
    channel = colorize(msg.channel, color_from_string(msg.channel))

    if msg.sender == "you" or msg.sender == "You":
        print(f"> [{channel}] {msg.message}")
    else:
        print(f"{sender} [{channel}]: {msg.message}")


def receiver(msg: TellMessage | ChannelMessage):
    if isinstance(msg, TellMessage):
        server_print_tell(msg)
    elif isinstance(msg, ChannelMessage):
        server_print_channel(msg)


def print_state(_s: str) -> None:
    tfprint(f"Chat state: {STATE}")


# the same script is run both inside tf and as a standalone chat-window server

if __name__ == "__main__":
    run(socket_server(Socket.CHAT, sender, receiver))
else:
    init_tf()
