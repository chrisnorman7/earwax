from math import dist
from pathlib import Path
from typing import Callable

from pytest import raises

from earwax import Ambiance, Box, BoxLevel, Door, Game, Point, Portal


class CollideWorks(Exception):
    pass


class ActivateWorks(Exception):
    pass


def test_init(box: Box, box_level: BoxLevel) -> None:
    # First test the fixtures.
    assert isinstance(box, Box)
    assert isinstance(box_level, BoxLevel)
    assert box_level.box is box
    assert box_level.x == 0.0
    assert box_level.y == 0.0
    assert box_level.bearing == 0
    assert box_level.current_box is None
    assert box_level.ambiances == []


def test_set_coordinates(box_level: BoxLevel) -> None:
    box_level.set_coordinates(3.0, 4.0)
    assert box_level.x == 3.0
    assert box_level.y == 4.0
    box_level.set_coordinates(5.8, 10.9)
    assert box_level.x == 5.8
    assert box_level.y == 10.9


def test_set_bearing(box_level: BoxLevel) -> None:
    box_level.set_bearing(45)
    assert box_level.bearing == 45
    box_level.set_bearing(23)
    assert box_level.bearing == 23


def test_register_ambiance(box_level: BoxLevel) -> None:
    a: Ambiance = Ambiance(box_level, 0.0, 0.0, Path('sound.wav'))
    box_level.register_ambiance(a)
    assert box_level.ambiances == [a]
    b: Ambiance = Ambiance(box_level, 2.9, 3.8, Path('other.wav'))
    box_level.register_ambiance(b)
    assert box_level.ambiances == [a, b]


def test_collide(box_level: BoxLevel, box: Box) -> None:
    box_level.collide(box)

    @box.event
    def on_collide() -> None:
        raise CollideWorks()

    with raises(CollideWorks):
        box_level.collide(box)


def test_move(box: Box, box_level: BoxLevel) -> None:
    # Let's make sure we've got pytest configured properly.
    assert box_level.x == 0.0
    assert box_level.y == 0.0
    m: Callable[[], None] = box_level.move()
    m()
    assert box_level.x == 0.0
    assert box_level.y == 1.0
    m()
    assert box_level.x == 0.0
    assert box_level.y == 2.0
    box_level.set_bearing(90)
    m()
    assert box_level.x == 1.0
    assert box_level.y == 2.0
    m()
    assert box_level.x == 2.0
    assert box_level.y == 2.0


def test_turn(box_level: BoxLevel) -> None:
    t: Callable[[], None] = box_level.turn(90)
    t()
    assert box_level.bearing == 90
    t()
    assert box_level.bearing == 180
    t()
    assert box_level.bearing == 270
    t()
    assert box_level.bearing == 0


def test_activate(game: Game, box: Box, box_level: BoxLevel) -> None:
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
    b: Box = Box(Point(0, 0), Point(0, 0), door=d, parent=box)
    assert dist(
        (box_level.x, box_level.y), (b.bottom_left.x, b.bottom_left.y)
    ) < 2.0
    assert box.get_containing_box(Point(box_level.x, box_level.y)) is b
    assert b.door is d
    a()
    assert d.open is False
    a()
    assert d.open is True
    destination: Box = Box(Point(0, 0), Point(15, 15))
    l: BoxLevel = BoxLevel(game, destination)
    b.door = None
    p: Portal = Portal(l, Point(14, 15))
    b.portal = p
    game.push_level(box_level)
    assert game.level is box_level
    box_level.set_bearing(55)
    a()
    assert game.level is l
    assert l.x == 14
    assert l.y == 15
    assert l.bearing == 55
    game.replace_level(box_level)
    p.bearing = 32
    a()
    assert l.bearing == 32
