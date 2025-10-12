from enum import StrEnum
import json
import re
from typing import Annotated, Literal
from pydantic import BaseModel, BeforeValidator, ValidationError

from py.color import (
    ANSI_BLUE,
    ANSI_BRIGHT_BLUE,
    ANSI_BRIGHT_CYAN,
    ANSI_BRIGHT_MAGENTA,
    ANSI_BRIGHT_WHITE,
    ANSI_BRIGHT_YELLOW,
    ANSI_CYAN,
    ANSI_GREEN,
    ANSI_MAGENTA,
    ANSI_RED,
    ANSI_YELLOW,
    Color,
    colorize_tf,
)
from py.tfutils import TriggerMatching, tfeval, tfprint

SKILLS_SPELLS_FILE = "py/skills_spells.json"

# $ jq '[.[] | .cast_type] | unique' skills_spells.json
# and .damage_type


class DamageType(StrEnum):
    ACID = "acid"
    ASPHYXIATION = "asphyxiation"
    COLD = "cold"
    ELECTRICITY = "electricity"
    FIRE = "fire"
    MAGICAL = "magical"
    PHYSICAL = "physical"
    POISON = "poison"
    PSIONIC = "psionic"


class CastType(StrEnum):
    ACID = "acid"
    ALCHEMY = "alchemy"
    ASPHYXIATION = "asphyxiation"
    CHANNELLING = "channelling"
    CHAOS = "chaos"
    COLD = "cold"
    CONTROL = "control"
    DEATH = "death"
    DESTRUCTION = "destruction"
    DISPEL = "dispel"
    ELECTRICITY = "electricity"
    EVIL = "evil"
    FIRE = "fire"
    HARM = "harm"
    HEAL = "heal"
    HELP = "help"
    HOLY = "holy"
    INFORMATION = "information"
    MAGICAL = "magical"
    POISON = "poison"
    PROTECTION = "protection"
    PSIONIC = "psionic"
    RIFT = "rift"
    RUNES = "runes"
    SONGS = "songs"
    SPECIAL = "special"
    TELEPORTATION = "teleportation"
    TRANSFORMATION = "transformation"
    VORTEX = "vortex"


DAMAGE_TYPE_COLORS: dict[DamageType | None, tuple[Color | None, Color | None]] = {
    DamageType.ACID: (ANSI_GREEN, None),
    DamageType.ASPHYXIATION: (ANSI_BRIGHT_MAGENTA, None),
    DamageType.COLD: (ANSI_BRIGHT_CYAN, None),
    DamageType.ELECTRICITY: (ANSI_BRIGHT_BLUE, None),
    DamageType.FIRE: (ANSI_RED, None),
    DamageType.MAGICAL: (ANSI_BRIGHT_YELLOW, None),
    DamageType.PHYSICAL: (ANSI_YELLOW, None),
    DamageType.POISON: (ANSI_GREEN, None),
    DamageType.PSIONIC: (ANSI_BRIGHT_BLUE, None),
}

CAST_TYPE_COLORS: dict[CastType | None, tuple[Color | None, Color | None]] = {
    CastType.ACID: (ANSI_GREEN, None),
    CastType.ALCHEMY: (None, None),
    CastType.ASPHYXIATION: (ANSI_BRIGHT_MAGENTA, None),
    CastType.CHANNELLING: (None, None),
    CastType.CHAOS: (None, None),
    CastType.COLD: (ANSI_BRIGHT_CYAN, None),
    CastType.CONTROL: (None, None),
    CastType.DEATH: (None, None),
    CastType.DESTRUCTION: (None, None),
    CastType.DISPEL: (ANSI_BRIGHT_WHITE, None),
    CastType.ELECTRICITY: (ANSI_BRIGHT_BLUE, None),
    CastType.EVIL: (None, None),
    CastType.FIRE: (ANSI_RED, None),
    CastType.HARM: (None, None),
    CastType.HEAL: (ANSI_GREEN, None),
    CastType.HELP: (ANSI_BRIGHT_WHITE, None),
    CastType.HOLY: (ANSI_BRIGHT_WHITE, None),
    CastType.INFORMATION: (None, None),
    CastType.MAGICAL: (ANSI_BRIGHT_YELLOW, None),
    CastType.POISON: (ANSI_GREEN, None),
    CastType.PROTECTION: (ANSI_BRIGHT_WHITE, ANSI_BLUE),
    CastType.PSIONIC: (ANSI_BRIGHT_BLUE, None),
    CastType.RIFT: (ANSI_MAGENTA, None),
    CastType.RUNES: (ANSI_MAGENTA, None),
    CastType.SONGS: (ANSI_MAGENTA, None),
    CastType.SPECIAL: (None, None),
    CastType.TELEPORTATION: (ANSI_CYAN, None),
    CastType.TRANSFORMATION: (None, None),
    CastType.VORTEX: (None, None),
}

SPELL_NAME_COLORS: dict[str | None, tuple[Color, Color]] = {
    "acquisition": (ANSI_BRIGHT_WHITE, ANSI_RED),
    "destroy armour": (ANSI_BRIGHT_WHITE, ANSI_RED),
    "destroy weapon": (ANSI_BRIGHT_WHITE, ANSI_RED),
    "disintegrate": (ANSI_BRIGHT_WHITE, ANSI_RED),
    "immolate": (ANSI_BRIGHT_WHITE, ANSI_RED),
}


def maybe_int(value: str | int | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def before_casting_time(value: str | int | None) -> int | None:
    if value is None or isinstance(value, int):
        return value

    value = value.strip().replace(" rounds", "")
    return maybe_int(value)


class Spell(BaseModel):
    name: str
    is_skill: Literal[False]
    casting_time: Annotated[int | None, BeforeValidator(before_casting_time)] = None
    spell_vocals: str | None = None
    cast_type: CastType | None = None
    damage_type: DamageType | None = None
    spell_point_cost: Annotated[int | None, BeforeValidator(maybe_int)] = None


SPELLS: dict[str, Spell] = {}
SPELL_BY_VOCALS: dict[str, Spell] = {}


def get_spell_by_name(name: str) -> Spell | None:
    return SPELLS.get(name.lower())


def load_spells() -> None:
    global SPELLS

    with open(SKILLS_SPELLS_FILE, "r", encoding="utf-8") as f:
        raw_skills_spells = json.load(f)

    for name, data in raw_skills_spells.items():
        try:
            spell = Spell.model_validate(data)
            SPELLS[name.lower()] = spell
            if spell.spell_vocals:
                SPELL_BY_VOCALS[spell.spell_vocals] = spell
        except ValidationError:
            continue

    print(f"Loaded {len(SPELLS)} spells from {SKILLS_SPELLS_FILE}")


SPELL_CAST_RE = re.compile(r" '(.+)'\.?$")


def set_spell_name_by_vocals(vocals: str) -> None:
    spell = SPELL_BY_VOCALS.get(vocals)
    if spell:
        set_spell_name_by_spell(spell)
    else:
        tfeval("/set spell_name=0")


def get_spell_color(spell: Spell) -> tuple[Color | None, Color | None]:
    return (
        SPELL_NAME_COLORS.get(spell.name.lower())
        or DAMAGE_TYPE_COLORS.get(spell.damage_type)
        or CAST_TYPE_COLORS.get(spell.cast_type, (None, None))
    )


def set_spell_name_by_spell(spell: Spell) -> None:
    color, bg_color = get_spell_color(spell)
    colorized = colorize_tf(f"({spell.name})", color, bg_color)
    tfeval(f"/set spell_name={colorized}")


def test_spell(s: str) -> None:
    """
    Test function to print out the spell name and its properties.
    """
    spell = SPELLS.get(s.lower())
    if not spell:
        tfprint(f"Spell '{s}' not found in SPELLS.")
        return
    set_spell_name_by_spell(spell)
    tfeval("/eval /echo -p \\%{spell_name}")


def init_tf() -> None:
    load_spells()
    pattern = SPELL_CAST_RE.pattern.replace("$", "\\$")
    matching = TriggerMatching.REGEXP
    cmd = f"/def -p5 -m{matching} -t`{pattern}` spell_vocals = "
    cmd += "/python_call py.spells.set_spell_name_by_vocals \\%P1\\%; "
    cmd += '/if (spell_name!~"0") /substitute -p \\%PL \\%spell_name\\%;/endif'
    # \\%;/set spell_name=0
    tfprint(cmd)
    tfeval(cmd)
    tfprint("Loaded spells")


if __name__ == "__main__":
    load_spells()
else:
    init_tf()
