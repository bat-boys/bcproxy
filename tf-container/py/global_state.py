import re
from typing import NamedTuple, Self
from datetime import datetime
from py.tfutils import (
    parse_level,
    stringify,
    tfprint,
    tfeval,
    trigger,
    trigger_bcproxy,
)

from dataclasses import dataclass


@dataclass
class State:
    char_name: str | None
    char_level: int | None
    char_race: str | None
    hp: int
    hpmax: int
    sp: int
    spmax: int
    ep: int
    epmax: int
    last_hb_at: datetime | None
    cast_spell: str | None
    cast_duration: int | None
    cast_target: str | None
    eqset: str | None


GLOBAL_STATE = State(
    char_name=None,
    char_level=None,
    char_race=None,
    hp=0,
    hpmax=0,
    sp=0,
    spmax=0,
    ep=0,
    epmax=0,
    last_hb_at=None,
    cast_spell=None,
    cast_duration=None,
    cast_target=None,
    eqset=None,
)

# /trigger You are Dreoca, a level III valar.
# /trigger You are Astrax, a level I merfolk and your secondary is Ruska.

WHOAMI_RE = re.compile(
    r"^You are (.+), a level ([^ ]+) (.+?)( and your (primary|secondary) is (.+))?.$"
)


def whoami_cb(s: str):
    global GLOBAL_STATE
    if match := WHOAMI_RE.match(s):
        GLOBAL_STATE.char_name = match.group(1)
        GLOBAL_STATE.char_level = parse_level(match.group(2))
        GLOBAL_STATE.char_race = match.group(3)


# hpstatus 3 10 1 10 0 10
# hp/hpmax sp/spmax ep/epmax


class BCHPStatus(NamedTuple):
    hp: int
    hpmax: int
    sp: int
    spmax: int
    ep: int
    epmax: int

    @classmethod
    def from_s(cls, s: str) -> Self:
        return cls(*map(int, s.split(" ")))


def hpstatus_cb(s: str):
    try:
        hpstatus = BCHPStatus.from_s(s)
    except ValueError:
        return

    global GLOBAL_STATE
    GLOBAL_STATE.hp = hpstatus.hp
    GLOBAL_STATE.hpmax = hpstatus.hpmax
    GLOBAL_STATE.sp = hpstatus.sp
    GLOBAL_STATE.spmax = hpstatus.spmax
    GLOBAL_STATE.ep = hpstatus.ep
    GLOBAL_STATE.epmax = hpstatus.epmax

    update_status_sc()


def use_cb(s: str):
    cast_use_cb(s)


def cast_cb(s: str):
    cast_use_cb(s)


def cast_use_cb(s: str):
    """
    Cast and use messages are the same but due to how the trigger function
    works, each must have a separate callback function
    """
    global GLOBAL_STATE
    fields = s.split(" ")

    GLOBAL_STATE.cast_spell = fields[0].replace("_", " ")
    duration = int(fields[1])

    # batclient message has duration 0 if duration is unknown, in that
    # case reduce duration by one or let it stay None
    if duration > 0:
        updated_duration = duration
    elif GLOBAL_STATE.cast_duration is not None:
        updated_duration = GLOBAL_STATE.cast_duration - 1
    else:
        updated_duration = None

    GLOBAL_STATE.cast_duration = updated_duration

    update_status_cast()


def clear_cast():
    global GLOBAL_STATE
    GLOBAL_STATE.cast_spell = None
    GLOBAL_STATE.cast_duration = None
    GLOBAL_STATE.cast_target = None
    update_status_cast()


def cast_cancelled_cb(_s: str):
    clear_cast()


CAST_INFO_EMPTY_MATCH = "You are not doing anything at the moment."


def cast_info_empty_cb(_s: str):
    clear_cast()


CAST_STARTED_MATCH = "You start chanting."


def cast_started_cb(_s: str):
    tfeval("@cast info")


USE_STARTED_MATCH = "You start concentrating on the skill."


def use_started_cb(_s: str):
    tfeval("@cast info")


CAST_INFO_RE = re.compile(r"^You are (casting|using) '(.+?)'( at '(.+)')?.$")


def cast_info_cb(s: str):
    global GLOBAL_STATE
    if match := CAST_INFO_RE.match(s):
        GLOBAL_STATE.cast_spell = match.group(2)
        if target := match.group(4):
            GLOBAL_STATE.cast_target = target
        else:
            GLOBAL_STATE.cast_target = None
        update_status_cast()


# H:{colorhp}/<maxhp> [{diffhp}] S:{colorsp}/<maxsp> [{diffsp}] E:{colorep}/<maxep> [{diffep}] $:<cash> [{diffcash}] exp:<exp> [{diffexp}] eqset:<eqset>

SC_RE = re.compile(
    r"^H:(-?\d+)/(\d+) \[([-+]?\d*)] S:(-?\d+)/(\d+) \[([-+]?\d*)] E:(-?\d+)/(\d+) \[([-+]?\d*)] \$:(\d+) \[([-+]?\d*)] exp:(\d+) \[([-+]?\d*)] eqset:(.+)$"
)


def sc_cb(s: str):
    global GLOBAL_STATE
    if match := SC_RE.match(s):
        GLOBAL_STATE.hp = int(match.group(1))
        GLOBAL_STATE.hpmax = int(match.group(2))
        GLOBAL_STATE.sp = int(match.group(4))
        GLOBAL_STATE.spmax = int(match.group(5))
        GLOBAL_STATE.ep = int(match.group(7))
        GLOBAL_STATE.epmax = int(match.group(8))
        GLOBAL_STATE.eqset = match.group(14)

        update_status_sc()


def on_login(_s: str):
    """
    This function is called on LOGIN hook, defined in tfrc
    """
    tfeval("@whoami;sc")


def update_status_sc():
    """
    Update status line sc-slot with current state

    Max width is defined in init_tf /status_add command:
    - 5 characters for eqset name
    """
    status = f"""\
EQ:{stringify(GLOBAL_STATE.eqset):5} \
H:{GLOBAL_STATE.hp:4}/{GLOBAL_STATE.hpmax:4} \
S:{GLOBAL_STATE.sp:4}/{GLOBAL_STATE.spmax:4} \
E:{GLOBAL_STATE.ep:3}/{GLOBAL_STATE.epmax:3} \
| """
    tfeval(f"/set status_row_sc={status}")


def update_status_cast():
    status = f"""\
{stringify(GLOBAL_STATE.cast_duration):>2} \
{stringify(GLOBAL_STATE.cast_spell, "", " ")}\
{stringify(GLOBAL_STATE.cast_target, "at ")}"""
    tfeval(f"/set status_row_cast={status}")


def print_state(_s: str):
    tfprint(f"state: {GLOBAL_STATE}")


def init_tf():
    trigger_bcproxy("hpstatus", hpstatus_cb)
    trigger_bcproxy("cast", cast_cb)
    trigger_bcproxy("use", use_cb)
    trigger_bcproxy("cast_cancelled", cast_cancelled_cb, simple=True)
    trigger(WHOAMI_RE, whoami_cb)
    trigger(CAST_INFO_EMPTY_MATCH, cast_info_empty_cb)
    trigger(CAST_STARTED_MATCH, cast_started_cb)
    trigger(USE_STARTED_MATCH, use_started_cb)
    trigger(CAST_INFO_RE, cast_info_cb)
    trigger(SC_RE, sc_cb)

    tfeval("/status_add -c status_row_sc:45 status_row_cast::BCrgb330 :1 @more:8:Br")


init_tf()
