"""Test the Box class."""

from typing import List, Optional

from earwax import (
    Box,
    BoxBounds,
    BoxLevel,
    BoxTypes,
    Door,
    Game,
    NotADoor,
    Point,
    Portal,
    SoundManager,
)
from pytest import raises


def test_init(box_level: BoxLevel, game: Game, box: Box) -> None:
    """Test that boxes initialise properly."""
    assert isinstance(box, Box)
    assert box.reverb is None
    assert isinstance(box.sound_manager, SoundManager)
    assert box.sound_manager.name == "Untitled sound manager"
    assert box.game is game
    assert box.start == Point(1, 2, 3)
    assert box.end == Point(4, 5, 6)
    assert box.type is BoxTypes.empty
    assert box.data is None
    assert box.box_level is None
    box = Box(game, box.start, box.end, box_level=box_level)
    assert box.box_level is box_level
    assert box_level.boxes == [box]


def test_contains_point(game: Game) -> None:
    """Test Box.contains_point."""
    b: Box = Box(game, Point(0, 0, 0), Point(0, 0, 0))
    assert b.contains_point(Point(0, 0, 0)) is True
    b.end = Point(5, 5, 0)
    assert b.contains_point(Point(3, 3, 0)) is True
    assert not b.contains_point(Point(55, 54, 52))
    assert not b.contains_point(Point(-3, -4, 0))
    assert not b.contains_point(Point(-1, 4, 5))
    assert not b.contains_point(Point(3, 7, 2))
    b = Box(game, Point(0, 0, 0), Point(5, 5, 5))
    assert b.contains_point(b.bounds.bottom_back_left)
    assert b.contains_point(b.bounds.bottom_front_left)
    assert b.contains_point(b.bounds.bottom_front_right)
    assert b.contains_point(b.bounds.top_back_left)
    assert b.contains_point(b.bounds.top_front_left)
    assert b.contains_point(b.bounds.top_front_right)
    assert b.contains_point(b.bounds.top_back_right)


def test_could_fit(game: Game) -> None:
    """Test the could_fit method."""
    c: Box = Box(game, Point(0, 0, 0), Point(5, 5, 5))
    b: Box = Box(game, c.start, c.end)
    assert c.could_fit(b) is True
    b = Box(game, c.start, c.bounds.top_back_left)
    assert c.could_fit(b) is True
    b = Box(game, c.bounds.bottom_front_left, c.bounds.top_front_left)
    assert c.could_fit(b) is True
    b = Box(game, c.bounds.bottom_front_right, c.bounds.top_front_right)
    assert c.could_fit(b) is True
    b = Box(game, c.bounds.bottom_back_right, c.bounds.top_back_right)
    assert c.could_fit(b) is True
    b = Box(game, c.start - Point(1, 1, 1), c.end)
    assert c.could_fit(b) is False
    b = Box(game, c.start, c.end + Point(1, 1, 1))
    assert c.could_fit(b) is False


def test_fitted_box(game: Game) -> None:
    """Test the FittedBox class."""
    southwest_box: Box = Box(game, Point(3, 5, 0), Point(8, 2, 0))
    northeast_box: Box = Box(game, Point(32, 33, 0), Point(80, 85, 5))
    middle_box: Box = Box(game, Point(14, 15, 2), Point(18, 22, 2))
    box: Box = Box.create_fitted(
        game, [middle_box, northeast_box, southwest_box]
    )
    assert box.start == southwest_box.start
    assert box.end == northeast_box.end


def test_create_fitted_padded(game: Game) -> None:
    """Ensure the pad_start and pad_end parameters work as expected."""
    a: Box = Box(game, Point(0, 0, 0), Point(3, 3, 3))
    b: Box = Box(
        game,
        a.bounds.bottom_back_right + Point(1, 0, 0),
        a.end + Point(3, 0, 0),
    )
    c: Box = Box.create_fitted(
        game, [a, b], pad_start=Point(-1, -2, -3), pad_end=Point(1, 2, 3)
    )
    assert c.start == Point(-1, -2, -3)
    assert c.end == Point(7, 5, 6)


def test_create_row(game: Game) -> None:
    """Test the create_row constructor."""
    start: Point = Point(1, 1, 0)
    boxes: List[Box] = Box.create_row(
        game, start, Point(5, 5, 4), 3, Point(1, 0, 0)
    )
    assert len(boxes) == 3
    first: Box
    second: Box
    third: Box
    first, second, third = boxes
    assert first.start == start
    assert first.end == Point(5, 5, 3)
    assert first.name is None
    assert first.type is BoxTypes.empty
    assert second.start == Point(6, 1, 0)
    assert second.end == Point(10, 5, 3)
    assert third.start == Point(11, 1, 0)
    assert third.end == Point(15, 5, 3)
    first, second, third = Box.create_row(
        game, Point(0, 0, 0), Point(3, 4, 5), 3, Point(0, 3, 0)
    )
    assert first.start == Point(0, 0, 0)
    assert first.end == Point(2, 3, 4)
    assert second.start == Point(0, 6, 0)
    assert second.end == Point(2, 9, 4)
    assert third.start == Point(0, 12, 0)
    assert third.end == Point(2, 15, 4)
    first, second, third = Box.create_row(
        game, start, Point(5, 5, 4), 3, Point(0, 0, 1)
    )
    assert first.start == start
    assert first.end == Point(5, 5, 3)
    assert second.start == Point(1, 1, 4)
    assert second.end == Point(5, 5, 7)
    assert third.start == Point(1, 1, 8)
    assert third.end == Point(5, 5, 11)


def test_create_row_named(game: Game) -> None:
    """Test creating a row of named rooms."""
    first: Box
    second: Box
    first, second = Box.create_row(
        game,
        Point(0, 0, 0),
        Point(3, 3, 3),
        2,
        Point(1, 0, 0),
        get_name=lambda i: f"Room {i + 1}",
    )
    assert first.name == "Room 1"
    assert second.name == "Room 2"


def test_create_row_on_create(game: Game) -> None:
    """Test the on_create parameter."""
    a: Box
    b: Box

    def on_create(b: Box) -> None:
        """Set a name."""
        if b.start == Point(0, 0, 0):
            b.name = "First Box"
        else:
            b.name = "Second Box"

    a, b = Box.create_row(
        game,
        Point(0, 0, 0),
        Point(1, 1, 1),
        2,
        Point(1, 0, 0),
        on_create=on_create,
    )
    assert a.name == "First Box"
    assert b.name == "Second Box"


def test_open(game: Game, door: Door) -> None:
    """Test door opening."""
    b: Box = Box(game, Point(0, 0, 0), Point(0, 0, 0))
    assert b.reverb is None

    @b.event
    def on_close() -> None:
        raise RuntimeError("This event should not have fired.")

    with raises(NotADoor):
        b.open()
    door.open = False
    b.data = door
    b.open()
    assert door.open is True

    @b.event
    def on_open() -> None:
        door.open = False

    b.open()
    assert door.open is False


def test_close(game: Game, door: Door) -> None:
    """Test closing doors."""
    b: Box = Box(game, Point(0, 0, 0), Point(0, 0, 0))

    @b.event
    def on_open() -> None:
        raise RuntimeError("This event should not have fired.")

    with raises(NotADoor):
        b.close()
    b.data = door
    b.close()
    assert door.open is False

    @b.event
    def on_close() -> None:
        door.open = True

    b.close()
    assert door.open is True


def test_bounds(game: Game) -> None:
    """Test the bounds of a box."""
    box: Box = Box(game, Point(1, 2, 3), Point(4, 5, 6))
    b: BoxBounds = box.bounds
    assert isinstance(b, BoxBounds)
    assert b.bottom_back_left == box.start
    assert b.bottom_front_left == Point(1, 5, 3)
    assert b.bottom_front_right == Point(4, 5, 3)
    assert b.bottom_back_right == Point(4, 2, 3)
    assert b.top_back_left == Point(1, 2, 6)
    assert b.top_front_left == Point(1, 5, 6)
    assert b.top_front_right == Point(4, 5, 6)
    assert b.top_back_right == Point(4, 2, 6)
    box = Box(game, Point(0, 0, 0), Point(5, 5, 5))
    b = box.bounds
    assert b.bottom_back_left == Point(0, 0, 0)
    assert b.bottom_front_left == Point(0, 5, 0)
    assert b.bottom_front_right == Point(5, 5, 0)
    assert b.bottom_back_right == Point(5, 0, 0)
    assert b.top_back_left == Point(0, 0, 5)
    assert b.top_front_left == Point(0, 5, 5)
    assert b.top_front_right == Point(5, 5, 5)
    assert b.top_back_right == Point(5, 0, 5)


def test_width(game: Game) -> None:
    """Test box.width."""
    b: BoxBounds = Box(game, Point(0, 1, 2), Point(5, 4, 3)).bounds
    assert b.width == 5


def test_depth(game: Game) -> None:
    """Test box depth."""
    b: BoxBounds = Box(game, Point(0, 1, 2), Point(5, 4, 3)).bounds
    assert b.depth == 3


def test_height(game: Game) -> None:
    """Test box height."""
    b: BoxBounds = Box(game, Point(0, 1, 2), Point(5, 4, 3)).bounds
    assert b.height == 1


def test_area(game: Game) -> None:
    """Test box area."""
    b: BoxBounds = Box(game, Point(0, 0, 0), Point(5, 5, 5)).bounds
    assert b.area == 25
    b = Box(game, Point(5, 6, 0), Point(9, 12, 7)).bounds
    assert b.area == 24


def test_volume(game: Game) -> None:
    """Test box volume."""
    b: BoxBounds = Box(game, Point(1, 2, 3), Point(10, 9, 8)).bounds
    assert b.volume == 315


def test_is_edge(game: Game) -> None:
    """Test the is_edge method."""
    b: BoxBounds = Box(game, Point(0, 0, 0), Point(3, 3, 3)).bounds
    assert b.is_edge(Point(0, 0, 0))
    assert b.is_edge(Point(0, 1, 2))
    assert b.is_edge(Point(2, 0, 0))


def test_is_wall(game: Game) -> None:
    """Test the is_wall method."""
    b: Box = Box(game, Point(1, 2, 3), Point(4, 5, 6))
    assert not b.is_wall(Point(1, 2, 3))
    assert not b.is_wall(Point(2, 3, 4))
    b.type = BoxTypes.solid
    assert b.is_wall(Point(1, 2, 3))
    assert b.is_wall(Point(2, 3, 4))
    b.type = BoxTypes.room
    assert b.is_wall(Point(1, 2, 3))
    assert not b.is_wall(Point(2, 3, 4))


def test_centre(game: Game) -> None:
    """Test the centre of a box."""
    b: Box = Box(game, Point(1, 1, 1), Point(4, 4, 4))
    assert b.centre == Point(2.5, 2.5, 2.5)
    b = Box(game, Point(0, 0, 0), Point(5, 5, 5))
    assert b.centre == Point(2.5, 2.5, 2.5)
    b = Box(game, Point(3, 4, 5), Point(7, 8, 9))
    assert b.centre == Point(5.0, 6.0, 7.0)


def test_sound_manager(game: Game) -> None:
    """Test making a sound manager."""
    b: Box = Box(game, Point(0, 0, 0), Point(3, 3, 3))
    assert b._sound_manager is None
    m: Optional[SoundManager] = b.sound_manager
    assert isinstance(m, SoundManager)
    assert m.default_position == b.centre
    assert b.reverb is None
    assert m.default_gain == game.config.sound.sound_volume.value
    assert m.default_looping is False
    assert m.default_reverb is None


def test_is_door(game: Game, box: Box) -> None:
    """Test the is_door property."""
    assert box.data is None
    assert not box.is_door
    b: Box[Door] = Box[Door](game, Point(0, 0, 0), Point(0, 0, 2), data=Door())
    assert b.is_door


def test_is_portal(game: Game, box: Box, box_level: BoxLevel) -> None:
    """Test the is_door property."""
    assert box.data is None
    assert not box.is_portal
    b: Box[Portal] = Box[Portal](
        game,
        Point(0, 0, 0),
        Point(0, 0, 2),
        data=Portal(box_level, Point(0, 0, 0)),
    )
    assert b.is_portal


def test_can_open(game: Game) -> None:
    """Test the can_open method."""
    d: Door = Door(open=False, can_open=lambda: False)
    box: Box[Door] = Box(game, Point(0, 0, 0), Point(5, 5, 5), data=d)
    box.open()
    assert d.open is False
    d.can_open = None
    box.open()
    assert d.open is True


def test_can_close(game: Game) -> None:
    """Test the can_close method."""
    d: Door = Door(open=True, can_close=lambda: False)
    box: Box[Door] = Box(game, Point(0, 0, 0), Point(5, 5, 5), data=d)
    box.close()
    assert d.open is True
    d.can_close = None
    box.close()
    assert d.open is False


def test_can_use(box_level: BoxLevel, game: Game, box: Box) -> None:
    """Test the can_use method of portals."""
    l: BoxLevel = BoxLevel(game)
    p: Portal = Portal(l, Point(52, 53, 54), can_use=lambda: False)
    start: Box[Portal] = Box(
        game, Point(0, 0, 0), Point(5, 5, 5), data=p, box_level=box_level
    )
    game.push_level(box_level)
    start.handle_portal()
    assert game.level is box_level
    p.can_use = None
    start.handle_portal()
    assert game.level is l
    assert l.coordinates == Point(52, 53, 54)


def test_get_nearest_point(game: Game) -> None:
    """Test the get_nearest_point method."""
    b: Box = Box(game, Point(1, 1, 1), Point(5, 5, 5))
    assert b.get_nearest_point(Point(0, 0, 0)) == b.start
    assert b.get_nearest_point(Point(0, 6, 0)) == b.bounds.bottom_front_left
    assert b.get_nearest_point(Point(6, 6, 0)) == b.bounds.bottom_front_right
    assert b.get_nearest_point(Point(6, 0, 0)) == b.bounds.bottom_back_right
    assert b.get_nearest_point(Point(0, 0, 6)) == b.bounds.top_back_left
    assert b.get_nearest_point(Point(0, 6, 6)) == b.bounds.top_front_left
    assert b.get_nearest_point(Point(6, 6, 6)) == b.end
    assert b.get_nearest_point(Point(6, 0, 6)) == b.bounds.top_back_right
    assert b.get_nearest_point(b.start) == b.start
    assert b.get_nearest_point(b.centre) == b.centre


def test_hash(game: Game) -> None:
    """Test that boxes can be hashed."""
    b: Box = Box(game, Point(1, 2, 3), Point(4, 5, 6))
    assert hash(b) == id(b)
    b2: Box = Box(game, Point(7, 8, 9), Point(10, 11, 12))
    assert hash(b2) == id(b2)
    assert hash(b2) != hash(b)
