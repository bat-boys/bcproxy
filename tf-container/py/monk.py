from py.tfutils import trigger, tfeval, tfprint

from py.global_state import get_state


def meditation_available_cb(s: str) -> None:
    global_state = get_state()
    tfeval(f"bell {global_state.char_name}")


def init_tf():
    trigger(
        "You feel in harmony with yourself, the universe and life in general.",
        meditation_available_cb,
    )
    tfprint("Loaded monk")


if __name__ != "__main__":
    init_tf()
