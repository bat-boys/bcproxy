from typing import Callable
from py.tfutils import tfeval, tfprint

import re

# This is an utility to enable capturing multiple lines from mud to a single
# callback function
#
# First you have to register the callback function with a name:
#
#     def disc_cb(s: list[str]) -> None:
#         ...
#
#     register_prefix_trigger("burgle_disc", disc_cb)
#
# Then in mud, have a command:
#
#     command with_prefix prefix "__PREFIX__$1 " $-2;prefix "__PREFIX__$1_ends " whoami
#
# And call with:
#
#     with_prefix burgle_disc la disc


PREFIX_TRIGGER_RE = re.compile(r"^__PREFIX__([a-z_]+?)(_ends)? (.+)$")
PREFIX_TRIGGER_STATE: dict[str, tuple[Callable[[list[str]], None], list[str]]] = {}


def register_prefix_trigger(name: str, fn: Callable[[list[str]], None]) -> None:
    tfprint(f"Registering prefix trigger: {name}")
    global PREFIX_TRIGGER_STATE
    PREFIX_TRIGGER_STATE[name] = (fn, [])


def cb(s: str) -> None:
    global PREFIX_TRIGGER_STATE
    match = PREFIX_TRIGGER_RE.match(s)
    if not match:
        return
    name, ends, s = match.groups()

    if name not in PREFIX_TRIGGER_STATE:
        if ends:
            tfprint(f"Prefix trigger {name} not registered!")
        return

    if ends:
        callback, args = PREFIX_TRIGGER_STATE[name]
        callback(args)
        PREFIX_TRIGGER_STATE[name] = (callback, [])
    else:
        _, args = PREFIX_TRIGGER_STATE[name]
        args.append(s)


def print_state(s: str) -> None:
    tfprint(str(PREFIX_TRIGGER_STATE))


def init_tf():
    callback_fn_str = "py.prefix_trigger.cb"
    callback_param = "\\%*"
    cmd = f"/def -i -agGL -p19 -mglob -t`__PREFIX__*` {callback_fn_str} = /python_call {callback_fn_str} {callback_param}"
    tfeval(cmd)
    tfprint("Loaded prefix_trigger")


if __name__ != "__main__":
    init_tf()
