from py.tfutils import tfeval


WALKING: dict[str, str] = {
    "^[7": "@nw",
    "^[8": "@n",
    "^[9": "@ne",
    "^[u": "@w",
    "^[i": "@walking_middle",
    "^[o": "@e",
    "^[j": "@sw",
    "^[k": "@s",
    "^[l": "@se",
    "^[y": "@u",
    "^[h": "@d",
}

CASTING: dict[str, str] = {
    # tabs
    "^[1": "/python_call casting.tab 1",
    "^[2": "/python_call casting.tab 2",
    "^[3": "/python_call casting.tab 3",
    "^[4": "/python_call casting.tab 4",
    "^[5": "/python_call casting.tab 5",
    # casts without target
    # these calls are not type safe, make sure that casting
    "^[q": "/python_call casting.cast q",
    "^[w": "/python_call casting.cast w",
    "^[e": "/python_call casting.cast e",
    "^[r": "/python_call casting.cast r",
    "^[t": "/python_call casting.cast t",
    "^[a": "/python_call casting.cast a",
    "^[s": "/python_call casting.cast s",
    "^[d": "/python_call casting.cast d",
    # targeted cast
    "^[Q": "/python_call casting.targeted_cast q",
    "^[W": "/python_call casting.targeted_cast w",
    "^[E": "/python_call casting.targeted_cast e",
    "^[R": "/python_call casting.targeted_cast r",
    "^[T": "/python_call casting.targeted_cast t",
    "^[A": "/python_call casting.targeted_cast a",
    "^[S": "/python_call casting.targeted_cast s",
    "^[D": "/python_call casting.targeted_cast d",
    # misc
    "^[z": "@cast stop",
}

PARTY_TARGETTING: dict[str, str] = {
    "^[7": "@nw",
}


def bind(keys: dict[str, str]):
    for key in keys:
        tfeval(f"/bind {key} = {keys[key]}")


def walking(_s: str | None = None):
    bind(WALKING)


def casting(_s: str | None = None):
    bind(CASTING)
