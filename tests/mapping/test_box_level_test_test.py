"""Test the BoxLevel class."""

from math import dist
from time import sleep
from typing import Callable, Optional

from pytest import raises
from synthizer import GlobalFdnReverb

from earwax import Box, BoxLevel, BoxTypes, Door, Game, Point, Portal


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
    assert isinstance(box_level.box, Box)
    assert box_level.coordinates == Point(1, 1, 1)
    assert box_level.bearing == 0
    assert box_level.current_box is None
    assert box_level.ambiances == []


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


def test_move(box: Box, box_level: BoxLevel) -> None:
    """Test movement."""
    m: Callable[[], None] = box_level.move()
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
        raise MoveWorks()

    with raises(MoveWorks):
        box_level.move()()
    # Shouldn't raise this time, because the target coordinates will be
    # invalid.
    box_level.coordinates.y = 1
    box_level.move(bearing=180)()


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


def test_activate(game: Game, box_level: BoxLevel, door: Door) -> None:
    """Test the enter key."""
    box: Box = box_level.box
    a: Callable[[], None] = box_level.activate()
    a()

    @box.event
    def on_activate() -> None:
        raise ActivateWorks()

    with raises(ActivateWorks):
        a()
    box.type = BoxTypes.solid
    with raises(ActivateWorks):
        a()
    box.type = BoxTypes.empty
    b: Box = Box(game, box.start, box.start, door=door, parent=box)
    assert dist(
        box_level.coordinates.coordinates, b.start.coordinates
    ) < 2.0
    assert box.get_containing_box(box_level.coordinates) is b
    assert b.door is door
    a()
    assert door.open is False
    a()
    assert door.open is True
    destination: Box = Box(game, Point(0, 0, 0), Point(15, 15, 0))
    l: BoxLevel = BoxLevel(game, destination)
    b.door = None
    p: Portal = Portal(l, Point(14, 15, 0))
    b.portal = p
    game.push_level(box_level)
    assert game.level is box_level
    box_level.set_bearing(55)
    a()
    assert game.level is l
    assert l.coordinates == Point(14, 15, 0)
    assert l.bearing == 55
    game.replace_level(box_level)
    # No need to reset coordinates, since each box level maintains its own
    # coordinates.
    p.bearing = 32
    a()
    assert l.bearing == 32


def test_move_fail(box_level: BoxLevel) -> None:
    """Test moves that should fail."""

    @box_level.event
    def on_move_fail(
        distance: float, vertical: Optional[float], bearing: Optional[int],
        coordinates: Point
    ) -> None:
        raise MoveFailWorks(distance, vertical, bearing, coordinates)

    box_level.coordinates.y = box_level.box.end.y - 1
    distance: float
    vertical: Optional[float]
    bearing: int
    point: Point
    box_level.move()()
    expected: Point = box_level.box.bounds.bottom_front_left + Point(0, 1, 0)
    with raises(MoveFailWorks) as exc:
        box_level.move()()
    distance, vertical, bearing, point = exc.value.args
    assert distance == 1.0
    assert vertical is None
    assert bearing == box_level.bearing
    assert point == expected
    box_level.set_bearing(180)
    expected = box_level.box.bounds.bottom_front_left + Point(0, 2, 8)
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
    box: Box = Box.create_fitted(game, [first, second, third])
    l: BoxLevel = BoxLevel(game, box)
    assert l.get_current_box() is first
    l.set_coordinates(second.start)
    assert l.get_current_box() is second
    doorstep: Box = Box(game, third.start, third.end, door=door, parent=third)
    assert doorstep in third.children
    assert doorstep.parent is third
    l.set_coordinates(doorstep.start)
    assert l.get_current_box() is doorstep


def test_get_angle_between(game: Game) -> None:
    """Test the get_angle_between method."""
    l: BoxLevel = BoxLevel(game, Box(game, Point(0, 0, 0), Point(0, 0, 0)))
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
