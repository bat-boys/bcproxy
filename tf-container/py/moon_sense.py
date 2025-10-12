from py.tfutils import tfprint, substitute_enumerable

MOON_SENSE: list[str] = [
    "A shimmering image of a waning gibbous moon appears in the center of the room.",
    "A shimmering image of a waxing gibbous moon appears in the center of the room.",
    "A shimmering image of a first quarter moon appears in the center of the room.",
    "A shimmering image of a third quarter moon appears in the center of the room.",
    "A shimmering image of a waning crescent moon appears in the center of the room.",
    "A shimmering image of a waxing crescent moon appears in the center of the room.",
    "A shimmering image of a dark moon appears in the center of the room.",
]


def init_tf():
    substitute_enumerable(MOON_SENSE)
    tfprint("Loaded moon sense")


if __name__ != "__main__":
    init_tf()
