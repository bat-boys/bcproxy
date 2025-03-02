from enum import IntEnum, StrEnum
from tf import eval  # type: ignore
from typing import Pattern


class TriggerMatching(StrEnum):
    REGEXP = "regexp"
    GLOB = "glob"
    SIMPLE = "simple"


class TriggerPriority(IntEnum):
    BCPROXY = 22  # from gag-bcproxy-tags.tf


def tfprint(s: str):
    for line in s.split("\n"):
        tfeval("/echo -p @{Crgb450}»@{n} " + line + "@{n}")


def tfeval(s: str):
    eval(s)


def trigger(
    pattern: str | Pattern[str],
    callback: str,
    priority: int = 10,
    gag: bool = False,
):
    if isinstance(pattern, Pattern):
        matching = TriggerMatching.REGEXP
        pattern = pattern.pattern.replace("\\", "\\\\").replace("$", "\\$")
    elif "*" in pattern:
        matching = TriggerMatching.GLOB
    else:
        matching = TriggerMatching.SIMPLE

    gag_flags = "-agGL" if gag else ""
    cmd = f"/def -i -F -p{priority} -m{matching} {gag_flags} -t`{pattern}` py.{callback} = /python_call py.{callback} \\%*"
    tfprint(cmd)
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


def initialize():
    # command with_triggers
    # ask trigger_$1_start about .;$-2;ask trigger_$1_end about .

    tfeval(
        """/def -agGL -p1 -mregexp -t`\
^Astounding!  You can see things no one else can see, such as trigger_(.+)_starts.$\
` trigger_enabler = /edit -c100 -agGL \\%P1"""
    )

    tfeval(
        """/def -F -agGL -p1 -mregexp -t`\
^Astounding!  You can see things no one else can see, such as trigger_(.+)_ends.$\
` trigger_disabler = /edit -c0 -an \\%P1"""
    )

    # "/def eqinfo = @with_triggers eqinfo_eqnumber eqnumber unworn \%*",
    # "/def -F -agGL -p10 -c0 -mregexp -t`"
    # + ".+[0-9]: (.+)\$"
    # + "` eqinfo_eqnumber = /python_call eqshoppe.eqinfo \%P1",
