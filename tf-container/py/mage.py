from typing import Pattern
from py.tfutils import gag, tfprint

GAGS: list[str | Pattern[str]] = [
    "Power flows from your staff to the spell.",
    "The magical powers of the staff surround you as it recognizes its rightful owner.",
    "The staff glows with shimmering white light.",
    "Your fine choice of components lowers the effort of the spell.",
    "You pull out * which bursts into a zillion technicolour sparkles!"
    "Your knowledge in elemental powers helps you to save the reagent for further use.",
    "You surreptitiously conceal your spell casting.",
    "You feel your staff touching your mind.",
]


def init_tf():
    gag(GAGS)
    tfprint("Loaded mage")


if __name__ != "__main__":
    init_tf()
