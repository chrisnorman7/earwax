"""Test story classes."""

from typing import Any, Dict

from earwax import Game, Point
from earwax.story import (RoomExit, RoomObject, StoryWorld, WorldAction,
                          WorldAmbiance, WorldMessages, WorldRoom)


def test_init(game: Game) -> None:
    """Test initialisation."""
    w: StoryWorld = StoryWorld(game)
    assert w.name == 'Untitled World'
    assert w.author == 'Unknown'
    assert w.main_menu_musics == []
    assert w.rooms == {}
    assert w.initial_room_id is None
    assert isinstance(w.messages, WorldMessages)


def test_dump(game: Game) -> None:
    """Test the dump method."""
    w: StoryWorld = StoryWorld(game, name='Test World', author='Earwax')
    room_1: WorldRoom = WorldRoom('first_room')
    room_1.world = w
    room_2: WorldRoom = WorldRoom('world_2')
    room_2.world = w
    w.rooms[room_1.id] = room_1
    w.rooms[room_2.id] = room_2
    w.initial_room_id = room_1.id
    exit_1: RoomExit = RoomExit(room_2.id)
    exit_1.location = room_1
    assert exit_1.destination is room_2
    room_1.exits.append(exit_1)
    exit_2: RoomExit = RoomExit(room_1.id)
    exit_2.location = room_2
    room_2.exits.append(exit_2)
    assert exit_2.destination is room_1
    object_1: RoomObject = RoomObject(
        id='object_1', position=Point(1, 2, 3), name='Object 1'
    )
    object_1.location = room_1
    room_1.objects[object_1.id] = object_1
    object_2: RoomObject = RoomObject(id='object_2')
    object_2.location = room_2
    room_2.objects[object_2.id] = object_2
    room_1.ambiances.append(WorldAmbiance('sound.wav'))
    object_1.ambiances.append(WorldAmbiance('move.wav'))
    object_1.actions.extend(
        [
            WorldAction(
                name='First Action', message='You test something.',
                sound='sound.wav'
            ), WorldAction(
                name='Second Action', message='Something else to test.',
                sound='move.wav'
            )
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
