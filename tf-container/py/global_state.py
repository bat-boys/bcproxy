import re
from typing import NamedTuple
from datetime import datetime
from py.tfutils import TriggerPriority, parse_level, stringify, tfprint, tfeval, trigger



class State(NamedTuple):
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
        GLOBAL_STATE = GLOBAL_STATE._replace(
            char_name=match.group(1),
            char_level=parse_level(match.group(2)),
            char_race=match.group(3),
        )


# hpstatus 3 10 1 10 0 10
# hp/hpmax sp/spmax ep/epmax

HPSTATUS_RE = re.compile(r"^\\\∴hpstatus (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)$")


def hpstatus_cb(s: str):
    global GLOBAL_STATE
    if match := HPSTATUS_RE.match(s):
        GLOBAL_STATE = GLOBAL_STATE._replace(
            hp=int(match.group(1)),
            hpmax=int(match.group(2)),
            sp=int(match.group(3)),
            spmax=int(match.group(4)),
            ep=int(match.group(5)),
            epmax=int(match.group(6)),
            last_hb_at=datetime.now(),
        )
        update_status_row()


CAST_RE = re.compile(r"^\\\∴(cast|use) (.+?) (\d+)$")


def cast_cb(s: str):
    global GLOBAL_STATE
    if match := CAST_RE.match(s):
        duration = int(match.group(3))

        # batclient message has duration 0 if duration is unknown, in that
        # case reduce duration by one or let it stay None
        if duration > 0:
            updated_duration = duration
        elif GLOBAL_STATE.cast_duration is not None:
            updated_duration = GLOBAL_STATE.cast_duration - 1
        else:
            updated_duration = None

        GLOBAL_STATE = GLOBAL_STATE._replace(
            cast_spell=match.group(2).replace("_", " "), cast_duration=updated_duration
        )
        update_status_row()


def clear_cast():
    global GLOBAL_STATE
    GLOBAL_STATE = GLOBAL_STATE._replace(
        cast_spell=None, cast_duration=None, cast_target=None
    )
    update_status_row()


CAST_CANCELLED_MATCH = "\\\\∴cast_cancelled"


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
        GLOBAL_STATE = GLOBAL_STATE._replace(cast_spell=match.group(2))
        if target := match.group(4):
            GLOBAL_STATE = GLOBAL_STATE._replace(cast_target=target)
        update_status_row()


# H:{colorhp}/<maxhp> [{diffhp}] S:{colorsp}/<maxsp> [{diffsp}] E:{colorep}/<maxep> [{diffep}] $:<cash> [{diffcash}] exp:<exp> [{diffexp}] eqset:<eqset>

SC_RE = re.compile(
    r"^H:(-?\d+)/(\d+) \[([-+]?\d*)] S:(-?\d+)/(\d+) \[([-+]?\d*)] E:(-?\d+)/(\d+) \[([-+]?\d*)] \$:(\d+) \[([-+]?\d*)] exp:(\d+) \[([-+]?\d*)] eqset:(.+)$"
)


def sc_cb(s: str):
    global GLOBAL_STATE
    if match := SC_RE.match(s):
        GLOBAL_STATE = GLOBAL_STATE._replace(
            hp=int(match.group(1)),
            hpmax=int(match.group(2)),
            sp=int(match.group(4)),
            spmax=int(match.group(5)),
            ep=int(match.group(7)),
            epmax=int(match.group(8)),
            eqset=match.group(14),
        )
        update_status_row()


def on_login(_s: str):
    """
    This function is called on LOGIN hook, defined in tfrc
    """
    tfeval("@whoami")


def update_status_row():
    status_row = f"""\
{stringify(GLOBAL_STATE.eqset, "EQ:", " ")}\
H:{GLOBAL_STATE.hp}/{GLOBAL_STATE.hpmax} \
S:{GLOBAL_STATE.sp}/{GLOBAL_STATE.spmax} \
E:{GLOBAL_STATE.ep}/{GLOBAL_STATE.epmax} \
| {stringify(GLOBAL_STATE.cast_duration, "", " ")}\
{stringify(GLOBAL_STATE.cast_spell, "", " ")}\
{stringify(GLOBAL_STATE.cast_target, "at ")}"""

    tfeval(f"/set global_status_row={status_row}")


def print_state(_s: str):
    tfprint(f"state: {GLOBAL_STATE}")


def init_tf():
    trigger(WHOAMI_RE, "global_state.whoami_cb")
    trigger(HPSTATUS_RE, "global_state.hpstatus_cb", TriggerPriority.BCPROXY)
    trigger(CAST_RE, "global_state.cast_cb", TriggerPriority.BCPROXY)
    trigger(
        CAST_CANCELLED_MATCH, "global_state.cast_cancelled_cb", TriggerPriority.BCPROXY
    )
    trigger(CAST_INFO_EMPTY_MATCH, "global_state.cast_info_empty_cb")
    trigger(CAST_STARTED_MATCH, "global_state.cast_started_cb")
    trigger(USE_STARTED_MATCH, "global_state.use_started_cb")
    trigger(CAST_INFO_RE, "global_state.cast_info_cb")
    trigger(SC_RE, "global_state.sc_cb")

    tfeval("/status_add -c global_status_row :1 @more:8:Br")


init_tf()
