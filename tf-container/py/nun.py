from py.tfutils import tfprint, substitute_enumerable

NUN_TURNS: list[str] = [
    "You should definitely turn more undeads.",
    "You should turn more undeads.",
    "You should turn some undeads in the near future.",
    "Your turn rate is good, keep up the good work.",
    "Your turn rate is excellent, the Gods are very pleased.",
    "Your devotions in turning is admirable, good work sister!",
    "You have turned a horde of undeads, Las is pleased.",
    "You have turned many undeads and thus made Las very happy.",
    "You are feared amongst the undeads, thy are in favour of Las.",
]


def init_tf():
    substitute_enumerable(NUN_TURNS)
    tfprint("Loaded nun")


if __name__ != "__main__":
    init_tf()
