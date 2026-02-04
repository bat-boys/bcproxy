import re
from typing import NamedTuple, Pattern, Self
from datetime import datetime
from py.tfutils import (
    gag,
    parse_level,
    stringify,
    tfprint,
    tfeval,
    trigger,
    trigger_bcproxy,
)
from dataclasses import dataclass
from py.prefix_trigger import register_prefix_trigger
from py.spells import get_spell_by_name
from py.color import Color, colorize_tf


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
    target: str | None


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
    target=None,
)

# /trigger You are Dreoca, a level III valar.
# /trigger You are Astrax, a level I merfolk and your secondary is Ruska.

WHOAMI_RE = re.compile(
    r"^You are (.+), a (level ([^ ]+) )?(.+?)( and your (primary|secondary) is (.+))?.$"
)


def get_state() -> State:
    """
    Get the global state object.
    """
    return GLOBAL_STATE


def whoami_cb(s: str):
    global GLOBAL_STATE
    if match := WHOAMI_RE.match(s):
        GLOBAL_STATE.char_name = match.group(1)
        GLOBAL_STATE.char_level = parse_level(match.group(2))
        GLOBAL_STATE.char_race = match.group(4)


def get_char_name() -> str | None:
    """
    Get character name from global state.
    """
    return GLOBAL_STATE.char_name


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

    # skill or spell name has either spaces or underscores, last word is duration
    GLOBAL_STATE.cast_spell = " ".join(s.split(" ")[:-1]).replace("_", " ")
    duration = int(s.split(" ")[-1])

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
    tfprint(
        colorize_tf(
            " -- skill/spell done -- ",
            Color(0xFF, 0x33, 0x33),
            Color(0x33, 0x33, 0x00),
        )
    )
    clear_cast()


CAST_INTERRUPTED_MATCH = "You interrupt the chant in order to start a new chant."


def cast_interrupted_cb(_s: str):
    tfprint(
        colorize_tf(
            " -- skill/spell interrupted -- ",
            Color(0xFF, 0x33, 0x33),
            Color(0x33, 0x33, 0x00),
        )
    )
    clear_cast()


CAST_INFO_EMPTY_MATCH = "You are not doing anything at the moment."


def cast_info_empty_cb(_s: str):
    clear_cast()


CAST_STARTED_MATCH = "You start chanting."
USE_STARTED_MATCH = "You start concentrating on the skill."


def cast_started_cb(_s: str):
    tfprint(
        colorize_tf(
            " -- spell started -- ", Color(0x33, 0xFF, 0x33), Color(0x33, 0x33, 0x00)
        )
    )
    tfeval("@with_prefix cast_info cast info")


# this has to be separate from cast_started_cb
def use_started_cb(_s: str):
    tfprint(
        colorize_tf(
            " -- skill started -- ", Color(0x33, 0xFF, 0x33), Color(0x33, 0x33, 0x00)
        )
    )
    tfeval("@with_prefix cast_info cast info")


CAST_INFO_RE = re.compile(r"^You are (casting|using) '(.+?)'( at '(.+)')?.$")


def cast_info_cb(s: list[str]):
    global GLOBAL_STATE
    if match := CAST_INFO_RE.match("".join(s)):
        spell_name = match.group(2)
        GLOBAL_STATE.cast_spell = spell_name
        spell = get_spell_by_name(spell_name)
        if spell and GLOBAL_STATE.cast_duration is None:
            GLOBAL_STATE.cast_duration = spell.casting_time
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


def set_target(target: str | None):
    global GLOBAL_STATE
    GLOBAL_STATE.target = target.lower() if target else None
    tfprint(f"Target: {GLOBAL_STATE.target}")


def get_target() -> str | None:
    return GLOBAL_STATE.target


def print_state(_s: str):
    tfprint(f"state: {GLOBAL_STATE}")


TARGET_MATCH = "You are now targetting *"
TARGET_HEAL_MATCH = "You are now target-healing *"


def target_cb(name: str):
    # remove last dot if present
    if name.endswith("."):
        name = name[:-1]
    set_target(name)


def target_heal_cb(name: str):
    # remove last dot if present
    if name.endswith("."):
        name = name[:-1]
    set_target(name)


CASTING_GAGS: list[str | Pattern[str]] = [
    "You surreptitiously conceal your spell casting.",
    "You skillfully cast the spell with haste.",
    "You skillfully cast the spell with greater haste.",
    "You interrupt the spell.",  # overlapping message from bcproxy
]


def init_tf():
    trigger_bcproxy("hpstatus", hpstatus_cb)
    trigger_bcproxy("cast", cast_cb)
    trigger_bcproxy("use", use_cb)
    trigger_bcproxy("cast_cancelled", cast_cancelled_cb, simple=True)
    trigger(WHOAMI_RE, whoami_cb)
    trigger(CAST_INFO_EMPTY_MATCH, cast_info_empty_cb, gag=True)
    trigger(CAST_STARTED_MATCH, cast_started_cb, gag=True)
    trigger(USE_STARTED_MATCH, use_started_cb, gag=True)
    trigger(CAST_INTERRUPTED_MATCH, cast_interrupted_cb, gag=True)
    trigger(TARGET_MATCH, target_cb, callback_param="\\%-4")
    trigger(TARGET_HEAL_MATCH, target_heal_cb, callback_param="\\%-4")
    gag(CASTING_GAGS)

    trigger(SC_RE, sc_cb)
    register_prefix_trigger("cast_info", cast_info_cb)

    tfeval("/status_add -c status_row_sc:45 status_row_cast::BCrgb330 :1 @more:8:Br")
    tfprint("Loaded global_state")


init_tf()
