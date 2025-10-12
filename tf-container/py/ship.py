"""
Ship navigation

Allows cruising to any coordinates in the same continent.

/def cr = /python_call py.ship.cruise $*

and then you can use /cr 1,2 to cruise to coordinates 1,2
"""

from enum import StrEnum
import re
from tf import eval as tfeval  # type: ignore
from typing import NamedTuple

from py.prefix_trigger import register_prefix_trigger
from py.tfutils import tfprint


class Cont(StrEnum):
    LAENOR = "laenor"
    LUCENTIUM = "lucentium"
    DESOLATHYA = "desolathya"
    ROTHIKGEN = "rothikgen"
    FURNACHIA = "furnachia"
    NEXUS = "nexus"


class Loc(NamedTuple):
    x: int
    y: int
    cont: Cont | None


CONTINENT_CHANGE: dict[tuple[Cont, Cont], str] = {
    (
        Cont.LAENOR,
        Cont.ROTHIKGEN,
    ): "daerwon,50 nw, 240 n, 60 ne, 424 e, 838 ne,rothikgen1",
    (Cont.LAENOR, Cont.DESOLATHYA): "daerwon,934 sw, 115 w,windhamkeep",
    (Cont.LAENOR, Cont.LUCENTIUM): "daerwon,538 sw, 1459 s,lucentium1",
    (
        Cont.LAENOR,
        Cont.FURNACHIA,
    ): "daerwon,155 sw, 185 s, 60 se, 628 e, 475 se,90 e,furnachia2",
    (Cont.DESOLATHYA, Cont.LAENOR): "windhamkeep, 29 se, 115 e, daerwon",
    (Cont.DESOLATHYA, Cont.ROTHIKGEN): "",
    (
        Cont.DESOLATHYA,
        Cont.LUCENTIUM,
    ): "windhamkeep,29 se,115 e,667 s,396 se,lucentium1",
    (
        Cont.DESOLATHYA,
        Cont.FURNACHIA,
    ): "windhamkeep, 29 se, 115 e, 779 ne, 185 s, 60 se, 628 e, 475 se, furnachia2",
    (
        Cont.ROTHIKGEN,
        Cont.LAENOR,
    ): "rothikgen1, 838 sw, 424 w, 60 sw, 240 s, daerwon",
    (Cont.ROTHIKGEN, Cont.DESOLATHYA): "",
    (Cont.ROTHIKGEN, Cont.LUCENTIUM): "",
    (Cont.ROTHIKGEN, Cont.FURNACHIA): "",
    (Cont.LUCENTIUM, Cont.LAENOR): "lucentium1,1459 n, 538 ne,daerwon",
    (Cont.LUCENTIUM, Cont.ROTHIKGEN): "",
    (
        Cont.LUCENTIUM,
        Cont.DESOLATHYA,
    ): "lucentium1,396 nw, 667 n, 115 w,windhamkeep",
    (
        Cont.LUCENTIUM,
        Cont.FURNACHIA,
    ): "lucentium1,1459 n, 383 ne, 185 s, 60 se, 628 e, 475 se, furnachia2",
    (
        Cont.FURNACHIA,
        Cont.LAENOR,
    ): "furnachia2,90 w, 475 nw, 628 w, 60 nw, 185 n, daerwon",
    (Cont.FURNACHIA, Cont.ROTHIKGEN): "",
    (Cont.FURNACHIA, Cont.DESOLATHYA): "",
    (Cont.FURNACHIA, Cont.LUCENTIUM): "",
}

# cruising only works if you're in main deck
WHEREAMI_RE = re.compile(
    r"^You are in '\(main deck\) .+' in .+ \(ship\) on the continent of (.+)\. \(Coordinates: ([0-9]+)x, ([0-9]+)y"
)
STATE: Loc | None = None


def whereami_cb(s: list[str]) -> None:
    global STATE
    if (match := WHEREAMI_RE.match(s[0])) and STATE:
        continent, x, y = match.groups()
        path = calculate_path(STATE, Loc(int(x), int(y), Cont(continent.lower())))
        tfprint(f"cruising {path}")
        tfeval(f"@gangway raise;ship launch;cruise {path}")
        STATE = None
    else:
        tfprint("Cruising works only on a ship's main deck, cannot parse whereami:")
        tfprint(str(s))
        tfprint("Or we don't have a destination set:")
        tfprint(str(STATE))


def cruise(s: str) -> None:
    global STATE

    if len(s.split(" ")) == 2:
        (x, y) = s.split(" ")
    elif len(s.split(",")) == 2:
        (x, y) = s.split(",")
    else:
        tfprint(f"No such area or cannot parse coordinates {s}")
        return
    x = re.findall(r"\d+", x)[0]
    y = re.findall(r"\d+", y)[0]

    STATE = Loc(int(x), int(y), None)

    # find out where we are now, start cruising if we're in a ship
    tfeval("@with_prefix ship_whereami whereami")


def calculate_path(target: Loc, cur: Loc) -> str:
    x_count = target.x - cur.x
    y_count = target.y - cur.y + 1
    x_dir = "e"
    y_dir = "s"

    if x_count < 0:
        x_count = x_count * -1
        x_dir = "w"
    if y_count < 0:
        y_count = y_count * -1
        y_dir = "n"

    # go diagonally as far as we can, and the rest straight

    diagonal_dir = y_dir + x_dir
    if x_count > y_count:
        diagonal_count = y_count
        straight_count = x_count - y_count
        straight_dir = x_dir
    else:
        diagonal_count = x_count
        straight_count = y_count - x_count
        straight_dir = y_dir

    return f"{diagonal_count} {diagonal_dir},{straight_count} {straight_dir}"


def init_tf():
    register_prefix_trigger("ship_whereami", whereami_cb)
    tfprint("Loaded ship.py")


if __name__ != "__main__":
    init_tf()
