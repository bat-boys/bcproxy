from asyncio import run
from typing import NamedTuple
from py.sockets import PartyUpdate, send_object, socket_client, socket_server, Socket
from py.tfutils import maybe_int, tfprint, trigger, TriggerPriority

from datetime import datetime


class Place(NamedTuple):
    x: int
    y: int


class Member(NamedTuple):
    name: str
    hp: int
    maxhp: int
    sp: int
    maxsp: int
    ep: int
    maxep: int
    place: Place
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
    stunned: int
    unconscious: int
    ambushed: bool
    updatedAt: float
    # source: MemberDataSource


class State(NamedTuple):
    members: frozenset[Member]
    places: dict[Place, Member]
    previousPlaces: dict[str, Place]  # str is member.name
    target: str | None
    pssHasMinions: bool
    manualMinions: bool


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
    party_creation_time: datetime

    @classmethod
    def from_str(cls, s: str):
        fields = s.split(" ")
        return cls(
            player=fields[0],
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
            formation=bool(fields[14]),
            member=bool(fields[15]),
            entry=bool(fields[16]),
            following=bool(fields[17]),
            leader=bool(fields[18]),
            linkdead=bool(fields[19]),
            resting=bool(fields[20]),
            idle=bool(fields[21]),
            invisible=bool(fields[22]),
            dead=bool(fields[23]),
            stunned=bool(fields[24]),
            unconscious=bool(fields[25]),
            party_exp=int(fields[26]),
            total_party_exp=int(fields[27]),
            party_length_in_seconds=int(fields[28]),
            party_creation_time=datetime.fromisoformat(fields[29]),
        )


PARTY_STATUS_GLOB = "\\∴party *"


def party_status_cb(s: str):
    bc_party_status_update = BCPartyStatusUpdate.from_str(s)

    tfprint(f"{bc_party_status_update}")


async def sender(msg: PartyUpdate):
    async with socket_client(Socket.PARTY) as (_, writer):
        await send_object(writer, msg)


def receiver(msg: PartyUpdate):
    pass


def init_tf():
    trigger(PARTY_STATUS_GLOB, party_status_cb, TriggerPriority.BCPROXY)


if __name__ == "__main__":
    run(socket_server(Socket.PARTY, sender, receiver))
else:
    init_tf()
