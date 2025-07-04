from typing import Iterable, NamedTuple
from hashlib import sha256


class Color(NamedTuple):
    r: int
    g: int
    b: int


# testing colors in terminal
# curl -s https://raw.githubusercontent.com/JohnMorales/dotfiles/master/colors/24-bit-color.sh | bash


RED = Color(0xFF, 0x00, 0x00)
GREEN = Color(0x00, 0xFF, 0x00)
YELLOW = Color(0xFF, 0xFF, 0x00)
WHITE = Color(0xFF, 0xFF, 0xFF)
ANSI_COLOR_RESET = "\033[0m"
TF_COLOR_RESET = "@{n}"

# values 0x00, 0x33, 0x66, 0x99, 0xCC, 0xFF

ANSI_BLACK = Color(0x00, 0x00, 0x00)
ANSI_RED = Color(0x99, 0x00, 0x00)
ANSI_GREEN = Color(0x00, 0x99, 0x00)
ANSI_YELLOW = Color(0x99, 0x99, 0x00)
ANSI_BLUE = Color(0x00, 0x00, 0x99)
ANSI_MAGENTA = Color(0x99, 0x00, 0x99)
ANSI_CYAN = Color(0x00, 0x99, 0x99)
ANSI_WHITE = Color(0x99, 0x99, 0x99)
ANSI_BRIGHT_BLACK = Color(0x99, 0x99, 0x99)
ANSI_BRIGHT_RED = Color(0xFF, 0x66, 0x66)
ANSI_BRIGHT_GREEN = Color(0x66, 0xFF, 0x66)
ANSI_BRIGHT_YELLOW = Color(0xFF, 0xFF, 0x66)
ANSI_BRIGHT_BLUE = Color(0x66, 0x66, 0xFF)
ANSI_BRIGHT_MAGENTA = Color(0xFF, 0x66, 0xFF)
ANSI_BRIGHT_CYAN = Color(0x66, 0xFF, 0xFF)
ANSI_BRIGHT_WHITE = Color(0xFF, 0xFF, 0xFF)


def colorize_maybe(
    s: str | None, color: Color | None, bg_color: Color | None = None
) -> str | None:
    return colorize(s, color, bg_color) if s is not None else None


def colorize(s: str, color: Color | None, bg_color: Color | None = None) -> str:
    """
    Colorize a string with the given color and background color for printing
    with ANSI.
    """
    if color is None and bg_color is None:
        return s

    def joined(xs: Iterable[str | int | None]) -> str:
        return ";".join((str(x) for x in xs if x is not None))

    color_str = f"38;2;{joined(color)}" if color is not None else None
    bg_color_str = f"48;2;{joined(bg_color)}" if bg_color is not None else None
    colors = joined([color_str, bg_color_str])

    begin = f"\033[{colors}m"
    return f"{begin}{s}{ANSI_COLOR_RESET}"


def tf_color(color: Color) -> str:
    """
    Round RGB values to nearest 0..5 and convert to TF color format.
    """

    def round_to_tf_value(value: int) -> int:
        return round(value / 255 * 5)

    r = round_to_tf_value(color.r)
    g = round_to_tf_value(color.g)
    b = round_to_tf_value(color.b)

    return f"rgb{r}{g}{b}"


def colorize_tf(s: str, color: Color | None, bg_color: Color | None = None) -> str:
    """
    Colorize a string with the given color and background color for printing
    inside TF
    """
    if color is None and bg_color is None:
        return s

    color_str = f"@{{C{tf_color(color)}}}" if color is not None else None
    bg_color_str = f"@{{Cbg{tf_color(bg_color)}}}" if bg_color is not None else None
    colors = "".join((x for x in (color_str, bg_color_str) if x is not None))

    return f"{colors}{s}{TF_COLOR_RESET}"


def color_from_string(s: str | None) -> Color | None:
    if s is None:
        return None

    hash_obj = sha256(s.encode())

    def compress(i: int) -> int:
        return int((i + 255) / 2)

    bytes = list(map(compress, hash_obj.digest()))

    return Color(bytes[0], bytes[1], bytes[2])


def green_red_gradient(
    n: int, n_max: int, all_red_abs: int, all_red_ratio: float
) -> Color:
    all_red = max(all_red_abs, int(n_max * all_red_ratio + 0.5))

    if n < all_red:
        return RED
    if n >= n_max:
        return GREEN

    # http://stackoverflow.com/a/340245
    # green is 0 and red 1, so invert the ratio to get maximum to be green
    # also, bottom 10% is already handled, so reduce 10% of maximum from both
    n_ratio = 1 - ((n - all_red) / (n_max - all_red))
    r = int(255 * n_ratio + 0.5)
    g = int(255 * (1 - n_ratio) + 0.5)
    return Color(r, g, 0)


def test():
    print("".join(colorize(s, color_from_string(s)) for s in "Hello, World!"))


if __name__ == "__main__":
    test()
