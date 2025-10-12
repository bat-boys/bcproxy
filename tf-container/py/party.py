from __future__ import annotations

from copy import copy
from asyncio import run
from typing import NamedTuple
from py.sockets import (
    Member,
    PartyMessage,
    Place,
    send_object,
    socket_client,
    socket_server,
    Socket,
)
from py.tfutils import maybe_int, tfprint, trigger, trigger_bcproxy
from py.color import RED, WHITE, YELLOW, Color, colorize, green_red_gradient
from py.global_state import get_char_name, set_target


#  Dornier 1429/1587 -158      Tuli 1473/1549  -76    Durtle 1861/1861
#  fol 131   29/  29        ldr 168   54/  54 *      fol 136  785/ 785
#   Byleth  483/ 483          Ruska  508/ 508
#  fol 291  313/1751        fol  40  946/1677
#                            Balron  483/ 483
#                           fol 286  330/1591


OUT_OF_FORMATION_COLOR = Color(204, 153, 255)

UNKNOWN_PLACES: list[Place] = [
    Place(0, 0),
    Place(0, 1),
    Place(0, 2),
    Place(0, 3),
    Place(1, 0),
    Place(2, 0),
    Place(3, 0),
]

EMPTY_PLACES: dict[Place, Member | None] = {
    Place(0, 0): None,
    Place(0, 1): None,
    Place(0, 2): None,
    Place(0, 3): None,
    Place(1, 0): None,
    Place(1, 1): None,
    Place(1, 2): None,
    Place(1, 3): None,
    Place(2, 0): None,
    Place(2, 1): None,
    Place(2, 2): None,
    Place(2, 3): None,
    Place(3, 0): None,
    Place(3, 1): None,
    Place(3, 2): None,
    Place(3, 3): None,
}

STATE = PartyMessage(set(), copy(EMPTY_PLACES), {}, None)


def clear_state() -> None:
    global STATE
    STATE = PartyMessage(set(), copy(EMPTY_PLACES), {}, None)


class BCPartyStatusUpdate(NamedTuple):
    player: str
    race: str
    gender: str
    level: int
    hp: int
    maxhp: int
    sp: int
    maxsp: int
    ep: int
    maxep: int
    party_name: str
    place_x: int | None
    place_y: int | None
    creator: str
    formation: bool
    member: bool
    entry: bool
    following: bool
    leader: bool
    linkdead: bool
    resting: bool
    idle: bool
    invisible: bool
    dead: bool
    stunned: bool
    unconscious: bool
    party_exp: int
    total_party_exp: int
    party_length_in_seconds: int
    party_creation_time: str  # TODO: parse datetime

    @classmethod
    def from_str(cls, s: str):
        fields = s.split(" ")
        return cls(
            player=fields[0].replace("_", " "),
            race=fields[1],
            gender=fields[2],
            level=int(fields[3]),
            hp=int(fields[4]),
            maxhp=int(fields[5]),
            sp=int(fields[6]),
            maxsp=int(fields[7]),
            ep=int(fields[8]),
            maxep=int(fields[9]),
            party_name=fields[10],
            place_x=maybe_int(fields[11]),
            place_y=maybe_int(fields[12]),
            creator=fields[13],
            formation=bool(int(fields[14])),
            member=bool(int(fields[15])),
            entry=bool(int(fields[16])),
            following=bool(int(fields[17])),
            leader=bool(int(fields[18])),
            linkdead=bool(int(fields[19])),
            resting=bool(int(fields[20])),
            idle=bool(int(fields[21])),
            invisible=bool(int(fields[22])),
            dead=bool(int(fields[23])),
            stunned=bool(int(fields[24])),
            unconscious=bool(int(fields[25])),
            party_exp=int(fields[26]),
            total_party_exp=int(fields[27]),
            party_length_in_seconds=int(fields[28]),
            party_creation_time=fields[29],
        )

    def to_status(self) -> tuple[str, Color | None, Color | None]:
        """
        status string, status color and name color
        """
        if self.unconscious:
            return "unc|?", RED, RED
        elif self.stunned:
            return "stu|?", RED, RED

        elif self.linkdead:
            return "ld", None, None
        elif self.dead:
            return "dead", None, None
        elif self.resting:
            return "rest", None, None

        elif self.invisible:
            return "invis", None, WHITE
        elif self.formation:
            return "form", None, WHITE
        elif self.member:
            return "mbr", None, OUT_OF_FORMATION_COLOR
        elif self.following and self.idle:
            return "fol", None, None
        elif self.following:
            return "fol", None, WHITE
        elif self.leader and self.idle:
            return "ldr", None, None
        elif self.leader:
            return "ldr", None, WHITE
        else:
            return "unk", RED, None

    def to_place(self) -> Place | None:
        if (
            self.place_x is not None
            and 1 <= self.place_x <= 3
            and self.place_y is not None
            and 1 <= self.place_y <= 3
        ):
            return Place(self.place_y, self.place_x)
        else:
            return None

    def to_member(self) -> Member:
        status, status_color, name_color = self.to_status()
        return Member(
            name=self.player,
            name_color=name_color,
            hp=self.hp,
            maxhp=self.maxhp,
            sp=self.sp,
            maxsp=self.maxsp,
            ep=self.ep,
            maxep=self.maxep,
            status=status,
            status_color=status_color,
            place=self.to_place(),
        )


def set_places() -> None:
    global STATE

    no_place: set[Member] = set()
    no_previous_place: set[Member] = set()
    new_places = copy(EMPTY_PLACES)

    # set places for members that have them

    for member in STATE.members:
        if member.place is not None:
            new_places[member.place] = member
            STATE.previous_places[member.name] = member.place
        else:
            no_place.add(member)

    # for others, check if they have a previous place
    # and set it if it is empty

    for member in no_place:
        place = STATE.previous_places.get(member.name, None)
        if place and new_places[place] is None:
            new_places[place] = member
        else:
            no_previous_place.add(member)

    # for others, set them to unknown places that are still available

    for member in no_previous_place:
        for place in UNKNOWN_PLACES:
            if new_places[place] is None:
                new_places[place] = member
                break

    STATE = STATE._replace(places=new_places)


def replace_state_member_by_name(member: Member) -> None:
    global STATE

    # equality check is not enough as member can be changed by other
    # fields except name

    for m in STATE.members:
        if m.name == member.name:
            STATE.members.remove(m)
            STATE.members.add(member)
            return

    STATE.members.add(member)


def party_cb(s: str) -> None:
    bc_party_status_update = BCPartyStatusUpdate.from_str(s)

    member = bc_party_status_update.to_member()
    replace_state_member_by_name(member)
    set_places()

    msg = PartyMessage(
        members=STATE.members,
        places=STATE.places,
        previous_places=STATE.previous_places,
        target=STATE.target,
    )

    run(sender(msg))


def partyleave_cb(s: str) -> None:
    me = get_char_name()

    if me and s.lower() == me.lower():
        clear_state()
    else:
        for m in STATE.members:
            if m.name == s.lower():
                STATE.members.remove(m)
                break

    set_places()

    msg = PartyMessage(
        members=STATE.members,
        places=STATE.places,
        previous_places=STATE.previous_places,
        target=STATE.target,
    )

    run(sender(msg))


async def sender(msg: PartyMessage) -> None:
    async with socket_client(Socket.PARTY) as (_, writer):
        await send_object(writer, msg)


def print_state(s: str) -> None:
    tfprint(str(STATE))


# party window


def receiver(msg: PartyMessage) -> None:
    draw(
        party_window_output(
            PartyMessage(
                members=msg.members,
                places=msg.places,
                previous_places=msg.previous_places,
                target=msg.target,
            )
        )
    )


def draw(s: str) -> None:
    print("\033c", end="")  # clear screen
    print(s)


def get_place_lines(state: PartyMessage, place: Place) -> tuple[str, str]:
    """
    For given member place, get the tf status line strings (two lines per member)

    <player name> <hp>/<hpmax> <hpdiff to max>
    <player state> <ep> <sp>/<spmax> <* if player is cast target>

    For example:
         Ruska  408/ 445  -37
      ldr  224 1404/1404

    :param member: member data
    :returns: Tuple of two strings for tf status lines
    """

    member = state.places.get(place, None)

    if member is None:
        return ("                        ", "                        ")

    name = colorize(f"{member.name[:8]: >9}", member.name_color)
    hp = colorize(
        f"{member.hp: >4}",
        green_red_gradient(member.hp, member.maxhp, 200, 0.2),
    )
    maxhp = f"{member.maxhp: >4}"
    hpdiff_str = member.hp - member.maxhp or " "
    hpdiff = colorize(f"{hpdiff_str: >5}", Color(0xEA, 0x22, 0x22))
    status = colorize(f"{member.status: >5}", member.status_color)
    is_target = colorize("*   ", YELLOW) if state.target == member.name else "    "
    ep_str = member.ep if member.ep is not None else "?"
    sp_str = member.sp if member.sp is not None else "?"
    maxsp_str = member.maxsp if member.maxsp is not None else "?"

    return (
        f"{name} {hp}/{maxhp}{hpdiff}",
        f"{status} {ep_str: >3} {sp_str: >4}/{maxsp_str: >4} {is_target}",
    )


def party_window_output(state: PartyMessage) -> str:
    s = ""
    # 0 last as we'll want the unknown places to bottom
    for y in (1, 2, 3, 0):
        col0 = get_place_lines(state, Place(y, 0))
        col1 = get_place_lines(state, Place(y, 1))
        col2 = get_place_lines(state, Place(y, 2))
        col3 = get_place_lines(state, Place(y, 3))

        s += f"{col0[0]} {col1[0]} {col2[0]} {col3[0]}\n"
        s += f"{col0[1]} {col1[1]} {col2[1]} {col3[1]}\n"

    return s


# targetting


def target_heal_cb(name: str) -> None:
    # remove last dot if present
    if name.endswith("."):
        name = name[:-1]
    target_by_name(name)


def target_by_name(name: str) -> None:
    global STATE

    # if target is not a member, clear target
    set_target(None)

    for member in STATE.members:
        if member.name.lower() == name.lower():
            STATE = STATE._replace(target=member.name)
            set_target(member.name)
            run(sender(STATE))
            return


def target_by_place(y: int, x: int) -> None:
    global STATE

    if x == -1 and y == -1:
        STATE = STATE._replace(target=None)
        run(sender(STATE))

    if not (0 <= x <= 3 and 0 <= y <= 3):
        return

    member = STATE.places.get(Place(y, x), None)
    if member:
        STATE = STATE._replace(target=member.name)
        set_target(member.name)
        run(sender(STATE))


def target(name_or_coords: str) -> None:
    # split name_or_coords
    splitted = name_or_coords.split()
    if len(splitted) == 1:
        # single name, try to target by name
        target_by_name(splitted[0])
    elif len(splitted) == 2:
        # two parts, try to parse as coordinates
        try:
            y = int(splitted[0])
            x = int(splitted[1])
            target_by_place(y, x)
        except ValueError:
            return


def init_tf() -> None:
    trigger_bcproxy("party", party_cb)
    trigger_bcproxy("partyleave", partyleave_cb)
    trigger("You are now target-healing *", target_heal_cb, callback_param="\\%-4")
    tfprint("Loaded party")


if __name__ == "__main__":
    run(socket_server(Socket.PARTY, sender, receiver))
else:
    init_tf()
