from asyncio import run
from dataclasses import dataclass
from enum import Enum
from py.sockets import (
    Socket,
    send_object,
    socket_client,
    socket_server,
    CastingTabMessage,
)
from py.color import WHITE, colorize
from py.spells import Spell, get_spell_by_name, get_spell_color
from py.tfutils import clear_and_print, tfeval, tfprint
from py.global_state import get_target

"""
casting.py

This module handles displaying spells in a tabbed window as well as
casting them.

Reporting needs this mud command:

    command zr quote 'grep -v "You are not doing" cast info' party report

Spells are added like this in tfrc:

    /python_call py.casting.add_casting_tab 1 heal
    /python_call py.casting.add_casting_tab_spell 1 q 1 cure light wounds
    /python_call py.casting.add_casting_tab_spell 1 w 1 cure critical wounds
    /python_call py.casting.add_casting_tab_spell 1 a -1 minor party heal
    /python_call py.casting.add_casting_tab_spell 1 s -1 major party heal

    /python_call py.casting.add_casting_tab 4 blast
    /python_call py.casting.add_casting_tab_spell 4 q 0 turn undead
    /python_call py.casting.add_casting_tab_spell 4 a 0 wither flesh

where first number (`1`, `2`) is the tab index, letters are the keys for casting
(see binds.py) and second number is the spell targetting type:
- -1 means spell does not accept a target (e.g. party heals)
- 0 means spell can be cast with or without target (e.g. offensive spells)
- 1 means spell requires a target (e.g. healing spells)
"""


class UseTarget(Enum):
    NEVER = -1
    EITHER = 0
    ALWAYS = 1


@dataclass
class CastingTab:
    title: str
    spells: dict[str, tuple[Spell, UseTarget]]


CASTING_TABS: dict[int, CastingTab] = {}
STATE: CastingTabMessage = CastingTabMessage(1, {}, {})


def add_casting_tab(s: str) -> None:
    global CASTING_TABS
    i, title = s.split(" ", 1)
    CASTING_TABS[int(i)] = CastingTab(title=title, spells={})


def add_casting_tab_spell(s: str) -> None:
    global CASTING_TABS
    i, key, require_target, spell_name = s.split(" ", 3)
    i = int(i)
    spell = get_spell_by_name(spell_name)

    if spell and i in CASTING_TABS:
        CASTING_TABS[i].spells[key] = (spell, UseTarget(int(require_target)))


def tab(s: str) -> None:
    global STATE
    i = int(s)
    if i in CASTING_TABS:
        STATE = CastingTabMessage(
            selected_tab=i,
            tab_titles={k: v.title for k, v in CASTING_TABS.items()},
            selected_tab_items={
                k: v[0].name for k, v in CASTING_TABS[i].spells.items()
            },
        )
        run(sender(STATE))


def get_spell(s: str) -> tuple[Spell | None, UseTarget | None]:
    tab = CASTING_TABS.get(STATE.selected_tab)
    if not tab:
        return (None, None)

    spell = tab.spells.get(s, (None, None))
    return spell


def cast(s: str) -> None:
    spell, use_target = get_spell(s)
    target = get_target()
    if not spell:
        return

    match use_target:
        case UseTarget.NEVER:
            tfeval(f"@cast {spell.name}")
        case UseTarget.EITHER:
            tfeval(f"@cast {spell.name}")
        case UseTarget.ALWAYS:
            tfeval(f"@cast {spell.name} at {target}")


def targeted_cast(s: str) -> None:
    target = get_target()
    spell, use_target = get_spell(s)
    if not spell:
        return

    match use_target:
        case UseTarget.NEVER:
            tfeval(f"@cast {spell.name};zr")
        case UseTarget.EITHER:
            tfeval(f"@cast {spell.name} at {target};zr")
        case UseTarget.ALWAYS:
            tfeval(f"@cast {spell.name} at {target};zr")


async def sender(msg: CastingTabMessage) -> None:
    async with socket_client(Socket.CASTING) as (_, writer):
        await send_object(writer, msg)


def receiver(msg: CastingTabMessage) -> None:
    header = " ".join(
        (
            colorize(f"{i}:{title}", WHITE if i == msg.selected_tab else None)
            for i, title in msg.tab_titles.items()
        )
    )
    rows = []
    for key, spell_name in msg.selected_tab_items.items():
        spell = get_spell_by_name(spell_name)
        fg, bg = get_spell_color(spell) if spell else (None, None)
        spell_name_colorized = colorize(spell_name, fg, bg)
        rows.append(f"{key} {spell_name_colorized}")

    clear_and_print("\n".join([header, *rows]))


def init_tf() -> None:
    tfprint("Loaded casting")


if __name__ == "__main__":
    run(socket_server(Socket.CASTING, sender, receiver))
else:
    init_tf()
