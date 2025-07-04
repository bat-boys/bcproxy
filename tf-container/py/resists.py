from enum import Enum
from typing import NamedTuple
from py.tfutils import (
    TriggerPriority,
    disable_trigger,
    enable_trigger,
    tfeval,
    tfprint,
    trigger,
)
from py.spells import DamageType, Spell, get_spell_by_name

"""
resists.py

This module reports mob resists to the party.

Spell hits with analyze gives these lines:

    You flap your arms and utter the magic words (blast vacuum)
    You pull out a bronze marble which bursts into a zillion technicolour sparkles!
    You watch with self-pride as your blast vacuum hits Grelnor.
    Grelnor screams in pain.

Spell and resist must be captured from separate lines, and mob shortname
is used for grouping resists together so that the result becomes like this:

    Astrax {report}: Elf ranger resists asphyxiation: 0, acid: 0%
"""


class Resist(Enum):
    SCREAM = 0
    WRITHE = 20
    SHUDDER = 40
    GRUNT = 60
    WINCE = 80
    SHRUG = 100


class MobResist(NamedTuple):
    name: str
    resists: dict[DamageType, Resist]


class State(NamedTuple):
    mob: str | None
    spell: Spell | None
    reported: MobResist | None


STATE = State(None, None, None)


def report(mob_resist: MobResist):
    rs = sorted(mob_resist.resists.items(), key=lambda x: x[1].value)
    resists_str = ", ".join(map(lambda r: f"{r[0]}: {r[1].value}%", rs))
    tfeval(f"@party report {mob_resist.name} resists {resists_str}")


def resists(resist: Resist, mob_raw: str):
    global STATE
    resists: dict[DamageType, Resist] = {}
    mob = mob_raw[12:]  # raw has "spec_spell: " in the beginning

    if (
        STATE.spell is not None
        and STATE.spell.damage_type is not None
        and STATE.mob is not None
        and STATE.mob == mob
    ):
        if STATE.reported and STATE.reported.name == mob:
            # this mob was shot already previously
            resists = STATE.reported.resists
            damage_type = STATE.spell.damage_type

            # new damtype, or changed resist to existing one
            if damage_type is not None and (
                damage_type not in resists or resists[damage_type] != resist
            ):
                resists[damage_type] = resist
                report(STATE.reported)
        else:
            # first or otherwise new mob
            damage_type = STATE.spell.damage_type
            resists[damage_type] = resist
            STATE = STATE._replace(reported=MobResist(mob, resists))
            if STATE.reported:
                report(STATE.reported)

        disable_resist_triggers()


def scream_cb(mob: str):
    resists(Resist.SCREAM, mob)


def writhe_cb(mob: str):
    resists(Resist.WRITHE, mob)


def shudder_cb(mob: str):
    resists(Resist.SHUDDER, mob)


def grunt_cb(mob: str):
    resists(Resist.GRUNT, mob)


def wince_cb(mob: str):
    resists(Resist.WINCE, mob)


def shrug_cb(mob: str):
    resists(Resist.SHRUG, mob)


def enable_resist_triggers():
    enable_trigger(scream_cb)
    enable_trigger(writhe_cb)
    enable_trigger(shudder_cb)
    enable_trigger(grunt_cb)
    enable_trigger(wince_cb)
    enable_trigger(shrug_cb)


def disable_resist_triggers():
    disable_trigger(scream_cb)
    disable_trigger(writhe_cb)
    disable_trigger(shudder_cb)
    disable_trigger(grunt_cb)
    disable_trigger(wince_cb)
    disable_trigger(shrug_cb)


def hits_cb(mob_and_spell: str):
    global STATE
    splitted = mob_and_spell.split(" hits ")
    if len(splitted) != 2:
        return

    spell_name, mob = splitted

    spell = get_spell_by_name(spell_name)
    STATE = STATE._replace(mob=mob.strip("."), spell=spell)

    enable_resist_triggers()


def is_dead_cb(mob: str) -> None:
    """
    Remove the stored resists if a mob with the same name dies.
    """
    global STATE
    if STATE.reported and STATE.reported.name == mob:
        STATE = STATE._replace(reported=None)
        disable_resist_triggers()


def print_state(_s: str) -> None:
    tfprint(str(STATE))


def init_tf():
    trigger(
        "spec_spell: You watch with self-pride as your *",
        hits_cb,
        TriggerPriority.BCPROXY,
        callback_param="\\%-7",
    )
    trigger(
        "spec_spell: * screams in pain.",
        scream_cb,
        TriggerPriority.BCPROXY,
        callback_param="\\%-L3",
    )
    trigger(
        "spec_spell: * writhes in agony.",
        writhe_cb,
        TriggerPriority.BCPROXY,
        callback_param="\\%-L3",
    )
    trigger(
        "spec_spell: * shudders from the force of the attack.",
        shudder_cb,
        TriggerPriority.BCPROXY,
        callback_param="\\%-L7",
    )
    trigger(
        "spec_spell: * grunts from the pain.",
        grunt_cb,
        TriggerPriority.BCPROXY,
        callback_param="\\%-L4",
    )
    trigger(
        "spec_spell: * winces a little from the pain.",
        wince_cb,
        TriggerPriority.BCPROXY,
        callback_param="\\%-L6",
    )
    trigger(
        "spec_spell: * shrugs off the attack.",
        shrug_cb,
        TriggerPriority.BCPROXY,
        callback_param="\\%-L4",
    )

    trigger(
        "* is DEAD, R.I.P.",
        is_dead_cb,
        callback_param="\\%-L3",
    )

    tfprint("Loaded resists")


if __name__ != "__main__":
    init_tf()
