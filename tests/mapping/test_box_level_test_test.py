"""Test the BoxLevel class."""

from math import dist
from time import sleep
from typing import Callable, Optional

from pytest import raises
from synthizer import GlobalFdnReverb

from earwax import (
    Box, BoxBounds, BoxLevel, BoxTypes, CurrentBox, Door, Game, Point, Portal)


class CollideWorks(Exception):
    """A test worked."""


class ActivateWorks(Exception):
    """The activate test worked."""


class MoveWorks(Exception):
    """Move test worked."""


class MoveFailWorks(Exception):
    """Move fail test worked."""


class TurnWorks(Exception):
    """Turn test worked."""


def test_init(box: Box, box_level: BoxLevel) -> None:
    """Test that box levels initialise properly."""
    # First test the fixtures.
    assert isinstance(box, Box)
    assert isinstance(box_level, BoxLevel)
    assert box_level.boxes == []
    assert box_level.coordinates == Point(0, 0, 0)
    assert box_level.bearing == 0
    assert box_level.current_box is None


def test_set_coordinates(box_level: BoxLevel) -> None:
    """Test that coordinates can be set."""
    p: Point = Point(3.0, 4.0, 5.0)
    box_level.set_coordinates(p)
    assert box_level.coordinates == p
    p = Point(5.8, 10.9, 15.4)
    box_level.set_coordinates(p)
    assert box_level.coordinates == p


def test_set_bearing(box_level: BoxLevel) -> None:
    """Test that the player's bearing can be set properly."""
    box_level.set_bearing(45)
    assert box_level.bearing == 45
    box_level.set_bearing(23)
    assert box_level.bearing == 23


def test_collide(box_level: BoxLevel, box: Box) -> None:
    """Test collisions."""
    box_level.collide(box, Point(0, 0, 0))

    @box.event
    def on_collide(coordinates: Point) -> None:
        assert coordinates == Point(3, 4, 5)
        raise CollideWorks()

    with raises(CollideWorks):
        box_level.collide(box, Point(3, 4, 5))


def test_move(game: Game, box_level: BoxLevel) -> None:
    """Test movement."""
    box: Box = Box(game, Point(1, 1, 1), Point(5, 5, 5))
    box_level.add_box(box)
    m: Callable[[], None] = box_level.move()
    box_level.set_coordinates(Point(1, 1, 1))
    m()
    assert box_level.coordinates == Point(1.0, 2.0, 1.0)
    m()
    assert box_level.coordinates == Point(1.0, 3.0, 1.0)
    box_level.set_bearing(90)
    m()
    assert box_level.coordinates == Point(2.0, 3.0, 1.0)
    m()
    assert box_level.coordinates == Point(3.0, 3.0, 1.0)
    box_level.move(bearing=180)()
    assert box_level.coordinates == Point(3.0, 2.0, 1.0)
    box_level.move(distance=0.0, vertical=1.0)()
    assert box_level.coordinates == Point(3.0, 2.0, 2.0)

    @box_level.event
    def on_move() -> None:
        assert box_level.coordinates == Point(3, 1, 2)
        raise MoveWorks()

    box_level.set_bearing(180)
    with raises(MoveWorks):
        m()
    # Shouldn't raise this time, because the target coordinates will be
    # invalid.
    m()

    @box_level.event
    def on_move_fail(
        distance: float, vertical: Optional[float], bearing: int,
        coordinates: Point
    ) -> None:
        assert distance == 1.0
        assert vertical is None
        assert bearing == 180
        assert coordinates == Point(3, 0, 2)
        raise MoveFailWorks()

    with raises(MoveFailWorks):
        m()


def test_turn(box_level: BoxLevel) -> None:
    """Test turning."""
    t: Callable[[], None] = box_level.turn(90)
    t()
    assert box_level.bearing == 90
    t()
    assert box_level.bearing == 180
    t()
    assert box_level.bearing == 270
    t()
    assert box_level.bearing == 0

    @box_level.event
    def on_turn() -> None:
        raise TurnWorks()

    with raises(TurnWorks):
        t()
    # Make sure the event fires after the new bearing is set.
    assert box_level.bearing == 90


def test_activate(
    game: Game, box_level: BoxLevel, door: Door, box: Box
) -> None:
    """Test the enter key."""
    box_level.add_box(box)
    a: Callable[[], None] = box_level.activate()
    a()
    box_level.set_coordinates(box.start)

    @box.event
    def on_activate() -> None:
        raise ActivateWorks()

    with raises(ActivateWorks):
        a()
    box.type = BoxTypes.solid
    with raises(ActivateWorks):
        a()
    box.type = BoxTypes.empty
    assert door.open is True
    b: Box = Box(game, box.start, box.start, data=door)
    box_level.add_box(b)
    assert dist(
        box_level.coordinates.coordinates, b.start.coordinates
    ) < 2.0
    assert box_level.get_containing_box(box_level.coordinates) is b
    assert b.is_door
    a()
    assert door.open is False
    a()
    assert door.open is True
    destination: Box = Box(game, Point(0, 0, 0), Point(15, 15, 0))
    l: BoxLevel = BoxLevel(game, boxes=[destination])
    p: Portal = Portal(l, Point(14, 15, 0))
    b.data = p
    game.push_level(box_level)
    assert game.level is box_level
    box_level.set_bearing(55)
    a()
    assert game.level is l
    assert l.coordinates == p.coordinates
    assert l.bearing == 55
    game.replace_level(box_level)
    # No need to reset coordinates, since each box level maintains its own
    # coordinates.
    p.bearing = 32
    a()
    assert l.bearing == 32


def test_move_fail(game: Game, box_level: BoxLevel) -> None:
    """Test moves that should fail."""
    box: Box = Box(game, Point(0, 0, 0), Point(5, 5, 5), box_level=box_level)

    @box_level.event
    def on_move_fail(
        distance: float, vertical: Optional[float], bearing: int,
        coordinates: Point
    ) -> None:
        raise MoveFailWorks(distance, vertical, bearing, coordinates)

    box_level.coordinates.y = box.end.y - 1
    distance: float
    vertical: Optional[float]
    bearing: int
    point: Point
    box_level.move()()
    expected: Point = box.bounds.bottom_front_left + Point(0, 1, 0)
    with raises(MoveFailWorks) as exc:
        box_level.move()()
    distance, vertical, bearing, point = exc.value.args
    assert distance == 1.0
    assert vertical is None
    assert bearing == box_level.bearing
    assert point == expected
    box_level.set_bearing(180)
    expected = box.bounds.bottom_front_left + Point(0, 2, 8)
    with raises(MoveFailWorks) as exc:
        box_level.move(distance=2.0, vertical=8.0, bearing=0)()
    distance, vertical, bearing, point = exc.value.args
    assert distance == 2.0
    assert vertical == 8.0
    assert bearing == 0
    assert point == expected


def test_get_current_box(game: Game, door: Door) -> None:
    """Test the get_current_box method."""
    first: Box
    second: Box
    third: Box
    first, second, third = Box.create_row(
        game, Point(0, 0, 0), Point(5, 5, 5), 3, Point(1, 0, 0)
    )
    box_level: BoxLevel = BoxLevel(game, boxes=[first, second, third])
    assert box_level.get_current_box() is first
    assert isinstance(box_level.current_box, CurrentBox)
    cb: CurrentBox = box_level.current_box
    assert cb.box is first
    assert cb.coordinates == box_level.coordinates
    box_level.set_coordinates(second.start)
    assert box_level.current_box is cb
    assert cb.box is first
    assert cb.coordinates == first.start
    assert box_level.get_current_box() is second
    assert isinstance(box_level.current_box, CurrentBox)
    cb = box_level.current_box
    assert cb.box is second
    assert cb.coordinates == second.start
    doorstep: Box[Door] = Box(
        game, third.bounds.bottom_front_right.copy(), third.end.copy(),
        data=door
    )
    box_level.add_box(doorstep)
    box_level.set_coordinates(doorstep.start)
    assert box_level.get_current_box() is doorstep
    parent: Box = Box(game, Point(0, 0, 0), Point(100, 100, 5))
    # Make a base for tracks to sit on.
    tracks: Box = Box(
        game, parent.start, parent.bounds.bottom_back_right + Point(0, 2, 0),
    )
    box_level = BoxLevel(game, boxes=[parent, tracks])
    assert box_level.get_containing_box(Point(0, 0, 0)) is tracks
    assert box_level.get_containing_box(Point(5, 5, 1)) is parent
    # Draw 2 parallel lines, like train tracks.
    b: BoxBounds = tracks.bounds
    southern_rail: Box = Box(game, b.bottom_back_left, b.bottom_back_right)
    northern_rail: Box = Box(game, b.bottom_front_left, b.bottom_front_right)
    box_level.add_box(southern_rail)
    box_level.add_box(northern_rail)
    assert box_level.get_containing_box(Point(5, 5, 0)) is parent
    assert box_level.get_containing_box(Point(0, 0, 0)) is southern_rail
    assert box_level.get_containing_box(Point(3, 2, 0)) is northern_rail
    assert box_level.get_containing_box(Point(1, 1, 0)) is tracks
    assert box_level.get_containing_box(Point(200, 201, 0)) is None


def test_get_angle_between(game: Game) -> None:
    """Test the get_angle_between method."""
    l: BoxLevel = BoxLevel(game)
    assert l.coordinates == Point(0, 0, 0)
    assert l.bearing == 0
    assert l.get_angle_between(Point(0, 1, 0)) == 0
    assert l.get_angle_between(Point(0, -1, 0)) == 180
    assert l.get_angle_between(Point(1, 1, 0)) == 45
    l.set_bearing(45)
    assert l.get_angle_between(Point(1, 1, 0)) == 0
    l.set_bearing(180)
    assert l.get_angle_between(Point(0, -1, 0)) == 0
    l.set_bearing(270)
    assert l.get_angle_between(Point(1, -1, 0)) == 225


def test_connect_reverb(reverb: GlobalFdnReverb, box_level: BoxLevel) -> None:
    """Test the connect_reverb method."""
    assert box_level.reverb is None
    box_level.connect_reverb(reverb)
    assert box_level.reverb is reverb


def test_disconnect_reverb(
    box_level: BoxLevel, reverb: GlobalFdnReverb
) -> None:
    """Test the disconnect_reverb method."""
    box_level.connect_reverb(reverb)
    box_level.disconnect_reverb()
    assert box_level.reverb is None


def test_handle_box(
    game: Game, reverb: GlobalFdnReverb, box_level: BoxLevel
) -> None:
    """Make sure boxes are handled properly."""
    start: Point = Point(0, 0, 0)
    end: Point = Point(3, 3, 3)
    a: Box = Box(game, start, end, reverb_settings={'gain': 0.1})
    b: Box = Box(game, start, end, reverb_settings={'gain': 0.5})
    box_level.connect_reverb(reverb)
    box_level.handle_box(a)
    sleep(0.5)
    assert reverb.gain == 0.1
    box_level.handle_box(b)
    sleep(0.5)
    assert reverb.gain == 0.5


def test_update_reverb(box_level: BoxLevel, reverb: GlobalFdnReverb) -> None:
    """Make sure we can update the reverb."""
    box_level.connect_reverb(reverb)
    box_level.update_reverb({'gain': 0.5})
    sleep(0.5)
    assert reverb.gain == 0.5
    box_level.update_reverb({'gain': 0.75, 't60': 0.5})
    sleep(0.5)
    assert reverb.gain == 0.75
    assert reverb.t60 == 0.5


def test_nearest_door(game: Game, door: Door) -> None:
    """Test Box.nearest_door."""
    room: Box = Box(game, Point(0, 0, 0), Point(3, 3, 3))
    box_level: BoxLevel = BoxLevel(game, boxes=[room])
    assert box_level.nearest_door(room.start) is None
    doorstep: Box = Box(
        game, room.end.copy(), room.end.copy(), data=door, box_level=box_level
    )
    assert box_level.nearest_door(room.start) is None
    assert box_level.nearest_door(room.start, same_z=False) is doorstep
    doorstep.start.z = room.start.z
    assert box_level.nearest_door(room.start) is doorstep
    assert box_level.nearest_door(room.start, same_z=False) is doorstep


def test_nearest_portal(game: Game) -> None:
    """Test Box.nearest_portal."""
    room: Box = Box(game, Point(0, 0, 0), Point(3, 3, 3))
    box_level: BoxLevel = BoxLevel(game, boxes=[room])
    assert box_level.nearest_portal(room.start) is None
    p: Portal = Portal(box_level, Point(0, 0, 0))
    assert box_level.nearest_portal(room.start) is None
    doorstep: Box[Portal] = Box(
        game, room.end.copy(), room.end.copy(), data=p, box_level=box_level
    )
    assert box_level.nearest_portal(room.start, same_z=False) is doorstep
    doorstep.start.z = room.start.z
    assert box_level.nearest_portal(room.start) is doorstep
    assert box_level.nearest_portal(room.start, same_z=False) is doorstep
    second_doorstep: Box[Portal] = Box(
        game, room.start.copy(), room.bounds.top_back_left.copy(), data=p,
        box_level=box_level
    )
    assert box_level.nearest_portal(room.start) is second_doorstep


def test_add_box(game: Game, box_level: BoxLevel, box: Box) -> None:
    """Test the add_box method."""
    cb: CurrentBox = CurrentBox(box.start, box)
    box_level.current_box = cb
    box_level.add_box(box)
    assert box.box_level is box_level
    assert box_level.boxes == [box]
    assert box_level.current_box is None
    box_level.current_box = cb
    box_2: Box = Box(
        game, box.bounds.bottom_front_right + Point(0, 1, 0),
        box.end + Point(0, 5, 0), box_level=box_level
    )
    assert box_level.boxes == [box, box_2]
    assert box_level.current_box is cb


def test_remove_box(box_level: BoxLevel, box: Box) -> None:
    """Test the remove_box method."""
    box_level.add_box(box)
    box_level.remove_box(box)
    assert box.box_level is None
    assert box_level.boxes == []
    box_level.add_box(box)
    box_level.set_coordinates(box.start.copy())
    box_level.get_current_box()
    assert isinstance(box_level.current_box, CurrentBox)
    box_level.remove_box(box)
    assert box_level.current_box is None
    assert box_level.boxes == []
    assert box.box_level is None
