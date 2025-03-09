from py.tfutils import gag, tfprint, substitute_enumerable

SENSECHARGE_STAFF: list[str] = [
    "shedding an eerie green light.",
    "shedding an eerie yellow light.",
    "shedding an eerie cyan light.",
    "shedding an eerie blue light.",
    "shedding an eerie magenta light.",
    "shedding an eerie red light.",
    "shedding an eerie bright green light.",
    "shedding an eerie bright yellow light.",
    "shedding an eerie bright cyan light.",
    "shedding an eerie bright blue light.",
    "shedding an eerie bright magenta light.",
    "shedding an eerie bright red light.",
]

GAG: list[str] = [
    "You concentrate on your staff...",
    "The sigla on your Staff of Druids glow softly,",
]


def init_tf():
    substitute_enumerable(SENSECHARGE_STAFF)
    gag(GAG)
    tfprint("Loaded druid")


if __name__ != "__main__":
    init_tf()
