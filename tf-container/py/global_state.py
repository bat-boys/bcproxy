import re
from typing import NamedTuple

from py.tfutils import parse_level, tfprint, tfeval, trigger


class State(NamedTuple):
    char_name: str | None
    char_level: int | None
    char_race: str | None


STATE = State(None, None, None)

WHOAMI_RE = re.compile(
    r"^You are (.+), a level ([^ ]+) (.+?)( and your (primary|secondary) is (.+))?.$"
)

# /trigger You are Dreoca, a level III valar.
# /trigger You are Astrax, a level I merfolk and your secondary is Ruska.


def whoami_cb(s: str):
    global STATE
    if match := WHOAMI_RE.match(s):
        STATE = STATE._replace(char_name=match.group(1))
        STATE = STATE._replace(char_level=parse_level(match.group(2)))
        STATE = STATE._replace(char_race=match.group(3))
        tfprint(f"state: {STATE}")


def on_login(_s: str):
    tfeval("@whoami")


def init_tf():
    trigger(WHOAMI_RE, "global_state.whoami_cb")


init_tf()
