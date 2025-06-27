from enum import IntEnum, StrEnum
import hashlib
import base64
from tf import eval  # type: ignore
from typing import Callable, Pattern


class TriggerMatching(StrEnum):
    REGEXP = "regexp"
    GLOB = "glob"
    SIMPLE = "simple"


class TriggerPriority(IntEnum):
    BCPROXY = 22
    BCPROXY_GAG = 20
    DEFAULT = 10
    SPELL_VOCAL = 5
    ENUMERATION = 4
    GAG = 3
    MONSTER = 2


def tfprint(s: str):
    for line in s.split("\n"):
        tfeval("/echo -p @{Crgb450}»@{n} " + line + "@{n}")


def tfeval(s: str):
    eval(s)


def trigger_bcproxy(
    bcproxy_message_type: str,
    callback: Callable[[str], None],
    simple: bool = False,
):
    if simple:
        pattern = f"#BCPROXY#{bcproxy_message_type}"
    else:
        pattern = f"#BCPROXY#{bcproxy_message_type} *"

    trigger(pattern, callback, TriggerPriority.BCPROXY, callback_param="\\%-1")


def get_callback_fn_str(callback: Callable[[str], None]) -> str:
    return f"{callback.__module__}.{callback.__name__}"


def trigger(
    pattern: str | Pattern[str],
    callback: Callable[[str], None],
    priority: int = TriggerPriority.DEFAULT,
    gag: bool = False,
    callback_param: str = "\\%*",
    disabled: bool = False,
):
    if isinstance(pattern, Pattern):
        matching = TriggerMatching.REGEXP
        pattern = pattern.pattern.replace("\\", "\\\\").replace("$", "\\$")
    elif "*" in pattern:
        matching = TriggerMatching.GLOB
    else:
        matching = TriggerMatching.SIMPLE

    gag_flags = "-ag" if gag else ""
    disable_flags = "-c0" if disabled else ""
    callback_fn_str = get_callback_fn_str(callback)
    cmd = f"/def -i -F -p{priority} -m{matching} {gag_flags} {disable_flags} -t`{pattern}` {callback_fn_str} = /python_call {callback_fn_str} {callback_param}"
    # tfprint(cmd)
    tfeval(cmd)


def enable_trigger(callback: Callable[[str], None]) -> None:
    callback_fn_str = get_callback_fn_str(callback)
    tfeval(f"/edit -c100 {callback_fn_str}")


def disable_trigger(callback: Callable[[str], None]) -> None:
    callback_fn_str = get_callback_fn_str(callback)
    tfeval(f"/edit -c0 {callback_fn_str}")


def short_hash(s: str | list[str]) -> str:
    if isinstance(s, list):
        s = " ".join(s)
    hashed = hashlib.sha256(s.encode()).digest()
    b64 = base64.urlsafe_b64encode(hashed).decode("utf-8")
    return b64[:12]


def substitute_enumerable(strs: list[str]) -> None:
    N = len(strs)
    hash = short_hash(strs)
    tf_match_str = "\\%{*}"
    priority = TriggerPriority.ENUMERATION
    for n, s in enumerate(strs):
        cmd = f"/def -i -p{priority} -msimple -t`{s}` enumerate_{hash}_{n} = /substitute {tf_match_str} ({n + 1}/{N})"
        tfeval(cmd)


def gag(patterns: str | Pattern[str] | list[str | Pattern[str]]) -> None:
    if not isinstance(patterns, list):
        patterns = [patterns]
    hash = short_hash(str(patterns))
    priority = TriggerPriority.GAG

    for n, pattern in enumerate(patterns):
        if isinstance(pattern, Pattern):
            matching = TriggerMatching.REGEXP
            pattern = pattern.pattern.replace("\\", "\\\\").replace("$", "\\$")
        elif "*" in pattern:
            matching = TriggerMatching.GLOB
        else:
            matching = TriggerMatching.SIMPLE

        cmd = f"/def -i -p{priority} -m{matching} -ag -t`{pattern}` gag_{hash}_{n}"
        tfeval(cmd)


def parse_level(s: str) -> int | None:
    roman_numerals = {
        "I": 101,
        "II": 102,
        "III": 103,
        "IV": 104,
        "V": 105,
        "VI": 106,
        "VII": 107,
        "VIII": 108,
        "IX": 109,
        "X": 110,
        "XI": 111,
        "XII": 112,
        "XIII": 113,
        "XIV": 114,
        "XV": 115,
        "XVI": 116,
        "XVII": 117,
        "XVIII": 118,
        "XIX": 119,
        "XX": 120,
    }

    try:
        return int(s)
    except ValueError:
        return roman_numerals.get(s, None)


def stringify(s: str | int | None, prefix: str = "", suffix: str = "") -> str:
    """
    Return a string with optional prefix and suffix or empty string if input is None
    """
    if s is None:
        return ""
    return f"{prefix}{s}{suffix}"


def maybe_int(s: str) -> int | None:
    try:
        return int(s)
    except ValueError:
        return None


def clear_and_print(s: str) -> None:
    print("\033c", end="")  # clear screen
    print(s)
