"""Test the BoxLevel class."""

from math import dist
from typing import Callable, Optional

from pytest import raises

from earwax import Box, BoxLevel, Door, Game, Point, Portal


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
    assert box_level.box is box
    assert box_level.coordinates == Point(0, 0, 0)
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
    # Let's make sure we've got pytest configured properly.
    assert box_level.coordinates == Point(0.0, 0.0, 0.0)
    assert box_level.box.end.z == 0.0
    box_level.box.end.z = 5.0
    m: Callable[[], None] = box_level.move()
    m()
    assert box_level.coordinates == Point(0.0, 1.0, 0.0)
    m()
    assert box_level.coordinates == Point(0.0, 2.0, 0.0)
    box_level.set_bearing(90)
    m()
    assert box_level.coordinates == Point(1.0, 2.0, 0.0)
    m()
    assert box_level.coordinates == Point(2.0, 2.0, 0.0)
    box_level.move(bearing=180)()
    assert box_level.coordinates == Point(2.0, 1.0, 0.0)
    box_level.move(distance=0.0, vertical=1.0)()
    assert box_level.coordinates == Point(2.0, 1.0, 1.0)

    @box_level.event
    def on_move() -> None:
        raise MoveWorks()

    with raises(MoveWorks):
        box_level.move()()
    # Shouldn't raise this time, because the target coordinates will be
    # invalid.
    box_level.coordinates.y = 0
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


def test_activate(game: Game, box: Box, box_level: BoxLevel) -> None:
    """Test the enter key."""
    a: Callable[[], None] = box_level.activate()
    a()

    @box.event
    def on_activate() -> None:
        raise ActivateWorks()

    with raises(ActivateWorks):
        a()
    box.wall = True
    with raises(ActivateWorks):
        a()
    box.wall = False
    d: Door = Door()
    b: Box = Box(Point(0, 0, 0), Point(0, 0, 0), door=d, parent=box)
    assert dist(
        box_level.coordinates.coordinates, b.start.coordinates
    ) < 2.0
    assert box.get_containing_box(box_level.coordinates) is b
    assert b.door is d
    a()
    assert d.open is False
    a()
    assert d.open is True
    destination: Box = Box(Point(0, 0, 0), Point(15, 15, 0))
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

    box_level.box.end.y = 1
    box_level.move()()
    with raises(MoveFailWorks) as exc:
        box_level.move()()
    assert exc.value.args == (1.0, None, None, Point(0, 2, 0))
    box_level.set_bearing(180)
    with raises(MoveFailWorks) as exc:
        box_level.move(distance=2.0, vertical=8.0, bearing=0)()
    assert exc.value.args == (2.0, 8.0, 0, Point(0, 3, 8))
