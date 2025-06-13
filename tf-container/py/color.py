from typing import Iterable, NamedTuple
from hashlib import sha256


class Color(NamedTuple):
    r: int
    g: int
    b: int


# testing colors in terminal
# curl -s https://raw.githubusercontent.com/JohnMorales/dotfiles/master/colors/24-bit-color.sh | bash


RED = Color(0xFF, 0, 0)
GREEN = Color(0, 0xFF, 0)
YELLOW = Color(0xFF, 0xFF, 0)
WHITE = Color(0xFF, 0xFF, 0xFF)


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
    reset = "\033[0m"
    return f"{begin}{s}{reset}"


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
