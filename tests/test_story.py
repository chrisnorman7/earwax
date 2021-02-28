"""Test story classes."""

from inspect import isgenerator
from typing import Any, Dict, Iterator, List

from earwax import Game
from earwax.story import (
    DumpablePoint,
    RoomExit,
    RoomObject,
    StoryWorld,
    WorldAction,
    WorldAmbiance,
    WorldMessages,
    WorldRoom,
)


def test_init(game: Game) -> None:
    """Test initialisation."""
    w: StoryWorld = StoryWorld(game)
    assert w.name == "Untitled World"
    assert w.author == "Unknown"
    assert w.main_menu_musics == []
    assert w.rooms == {}
    assert w.initial_room_id is None
    assert isinstance(w.messages, WorldMessages)


def test_dump(game: Game) -> None:
    """Test the dump method."""
    w: StoryWorld = StoryWorld(game, name="Test World", author="Earwax")
    room_1: WorldRoom = WorldRoom("first_room")
    w.add_room(room_1)
    assert w.initial_room is room_1
    room_2: WorldRoom = WorldRoom("world_2")
    w.add_room(room_2)
    assert w.initial_room is room_1
    exit_1: RoomExit = room_1.create_exit(room_2)
    assert exit_1.destination_id == room_2.id
    assert exit_1.destination is room_2
    assert exit_1 in room_1.exits
    assert exit_1.location is room_1
    exit_2: RoomExit = room_2.create_exit(room_1)
    assert exit_2.destination_id == room_1.id
    assert exit_2.destination is room_1
    assert exit_2 in room_2.exits
    object_1: RoomObject = room_1.create_object(
        id="object_1", position=DumpablePoint(1, 2, 3), name="Object 1"
    )
    assert object_1.location is room_1
    assert room_1.objects[object_1.id] is object_1
    object_2: RoomObject = room_2.create_object(id="object_2")
    assert object_2.location is room_2
    assert room_2.objects[object_2.id] is object_2
    room_1.ambiances.append(WorldAmbiance("sound.wav"))
    object_1.ambiances.append(WorldAmbiance("move.wav"))
    object_1.actions.extend(
        [
            WorldAction(
                name="First Action",
                message="You test something.",
                sound="sound.wav",
            ),
            WorldAction(
                name="Second Action",
                message="Something else to test.",
                sound="move.wav",
            ),
        ]
    )
    data: Dict[str, Any] = w.dump()
    w2: StoryWorld = StoryWorld.load(data, game)
    assert w2.initial_room_id == w.initial_room_id
    assert len(w2.rooms) == 2
    r1: WorldRoom
    r2: WorldRoom
    r1, r2 = w2.rooms.values()
    assert r1.world is w2
    assert r1.id == room_1.id
    assert r1.name == room_1.name
    assert r1.description == room_1.description
    assert r2.world is w2
    assert r2.id == room_2.id
    assert r2.name == room_2.name
    assert r2.description == room_2.description


def test_all_objects(game: Game) -> None:
    """Test the all_objects generator."""
    w: StoryWorld = StoryWorld(game)
    room_1: WorldRoom = WorldRoom()
    w.add_room(room_1)
    o1: RoomObject = room_1.create_object()
    o2: RoomObject = room_1.create_object()
    room_2: WorldRoom = WorldRoom()
    w.add_room(room_2)
    o3: RoomObject = room_2.create_object()
    room_3: WorldRoom = WorldRoom()
    w.add_room(room_3)
    o4: RoomObject = room_3.create_object()
    o5: RoomObject = room_3.create_object()
    i: Iterator[RoomObject] = w.all_objects()
    assert isgenerator(i)
    objects_list: List[RoomObject] = list(i)
    assert objects_list == [o1, o2, o3, o4, o5]
