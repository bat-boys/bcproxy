from py.tfutils import tfeval, tfprint

"""
next_command.py

This module manages a queue of commands associated with different keys.

First you have to add commands using the `add` function:

    /python_call py.next_command.add foo tell astrax moi
    /python_call py.next_command.add foo tell astrax hei

Then you can run the commands using the `run` function:

    /python_call py.next_command.run foo

First call will execute `tell astrax moi` and second
`tell astrax hei`.
"""

STATE: dict[str, list[str]] = {}
DONE: dict[str, list[str]] = {}


def run(s: str) -> None:
    global STATE, DONE

    if s in STATE:
        if len(STATE[s]) == 0:
            tfprint(f"No commands left for {s}.")
            return
        cmd = STATE[s].pop(0)
        DONE[s].append(cmd)
        tfeval(cmd)
        tfprint(f"Started: {cmd}")
        tfprint(f"Remaining: {STATE[s]}")


def add(s: str) -> None:
    global STATE, DONE

    key, cmd = s.split(" ", 1)
    if key not in STATE:
        STATE[key] = []
        DONE[key] = []

    STATE[key].append(cmd)


def reset(key: str) -> None:
    """
    Move all commands from DONE back to STATE for the given key.

    Retain order of commands in STATE.
    """
    global STATE, DONE

    if key in STATE:
        STATE[key] = [*DONE[key], *STATE[key]]
        DONE[key] = []
        tfprint(f"Reset commands for {key}: {STATE[key]}")


def init_tf() -> None:
    tfprint("Loaded next_command")


if __name__ != "__main__":
    init_tf()
