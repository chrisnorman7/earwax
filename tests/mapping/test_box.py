"""Test the Box class."""

from time import sleep
from typing import List

from pytest import raises
from synthizer import GlobalFdnReverb, PannerStrategy, Source3D, SynthizerError

from earwax import (Box, BoxBounds, BoxLevel, BoxTypes, Door, Game, NotADoor,
                    OutOfBounds, Point, Portal, SoundManager)


def test_init(game: Game, box: Box) -> None:
    """Test that boxes initialise properly."""
    assert isinstance(box, Box)
    assert box.reverb is None
    assert box.sound_manager is None
    assert box.game is game
    assert box.start == Point(1, 2, 3)
    assert box.end == Point(4, 5, 6)
    assert box.type is BoxTypes.empty
    b: Box = Box(game, box.start, box.end, parent=box)
    assert b.parent is box
    assert b in box.children
    assert b.reverb_settings == {}
    b = Box(game, box.start, box.end, reverb_settings={'gain': 0.5})
    assert b.reverb_settings == {'gain': 0.5}


def test_add_child(game: Game) -> None:
    """Test adding child boxes."""
    b: Box = Box(game, Point(0, 0, 0), Point(3, 3, 0))
    c: Box = Box(game, Point(1, 1, 0), Point(1, 1, 0), parent=b)
    assert c.parent is b
    assert b.children == [c]
    gc: Box = Box(game, Point(1, 1, 0), Point(1, 1, 0), parent=c)
    assert gc.parent is c
    assert c.children == [gc]
    broken: Box = Box(game, Point(-1, 0, 5), Point(-1, 0, -2))
    with raises(OutOfBounds) as exc:
        b.add_child(broken)
    assert exc.value.args == (b, broken)
    broken = Box(game, Point(10, 10, 10), Point(10, 10, 10))
    with raises(OutOfBounds) as exc:
        b.add_child(broken)
    assert exc.value.args == (b, broken)


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


def test_get_containing_child(game: Game) -> None:
    """Test Box.get_containing_box."""
    parent: Box = Box(game, Point(0, 0, 0), Point(100, 100, 5))
    # Make a base for tracks to sit on.
    tracks: Box = Box(
        game, parent.start, parent.bounds.bottom_back_right + Point(0, 2, 0),
        parent=parent
    )
    assert parent.get_containing_box(Point(0, 0, 0)) is tracks
    assert parent.get_containing_box(Point(5, 5, 1)) is parent
    # Draw 2 parallel lines, like train tracks.
    b: BoxBounds = tracks.bounds
    southern_rail: Box = Box(
        game, b.bottom_back_left, b.bottom_back_right, parent=tracks
    )
    northern_rail = Box(
        game, b.bottom_front_left, b.bottom_front_right, parent=tracks
    )
    assert parent.get_containing_box(Point(5, 5, 0)) is parent
    assert parent.get_containing_box(Point(0, 0, 0)) is southern_rail
    assert parent.get_containing_box(Point(3, 2, 0)) is northern_rail
    assert parent.get_containing_box(Point(1, 1, 0)) is tracks
    assert parent.get_containing_box(Point(200, 201, 0)) is None


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
        game, a.bounds.bottom_back_right + Point(1, 0, 0),
        a.end + Point(3, 0, 0)
    )
    c: Box = Box.create_fitted(
        game, [a, b],
        pad_start=Point(-1, -2, -3),
        pad_end=Point(1, 2, 3)
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
    first, second = Box.create_row(
        game, Point(0, 0, 0), Point(3, 3, 3), 2, Point(1, 0, 0),
        get_name=lambda i: f'Room {i + 1}'
    )
    assert first.name == 'Room 1'
    assert second.name == 'Room 2'


def test_create_row_on_create(game: Game) -> None:
    """Test the on_create parameter."""
    a: Box
    b: Box

    def on_create(b: Box) -> None:
        """Set a name."""
        if b.start == Point(0, 0, 0):
            b.name = 'First Box'
        else:
            b.name = 'Second Box'

    a, b = Box.create_row(
        game, Point(0, 0, 0), Point(1, 1, 1), 2, Point(1, 0, 0),
        on_create=on_create
    )
    assert a.name == 'First Box'
    assert b.name == 'Second Box'


def test_open(game: Game, door: Door) -> None:
    """Test door opening."""
    b: Box = Box(game, Point(0, 0, 0), Point(0, 0, 0))
    assert b.reverb_settings == {}
    assert b.reverb is None

    @b.event
    def on_close() -> None:
        raise RuntimeError('This event should not have fired.')

    with raises(NotADoor):
        b.open()
    door.open = False
    b.door = door
    b.open()
    assert door.open is True
    assert isinstance(b.sound_manager, SoundManager)
    assert isinstance(b.sound_manager.source, Source3D)
    assert b.reverb is None

    @b.event
    def on_open() -> None:
        door.open = False

    b.open()
    assert door.open is False
    b = Box(game, b.start, b.end, reverb_settings={'gain': 0.5}, door=b.door)
    b.door.open = False
    b.open()
    assert isinstance(b.reverb, GlobalFdnReverb)
    sleep(0.2)
    assert b.reverb.gain == b.reverb_settings['gain']


def test_close(game: Game, door: Door) -> None:
    """Test closing doors."""
    b: Box = Box(game, Point(0, 0, 0), Point(0, 0, 0))

    @b.event
    def on_open() -> None:
        raise RuntimeError('This event should not have fired.')

    with raises(NotADoor):
        b.close()
    b.door = door
    b.close()
    assert door.open is False
    assert isinstance(b.sound_manager, SoundManager)
    assert isinstance(b.sound_manager.source, Source3D)

    @b.event
    def on_close() -> None:
        door.open = True

    b.close()
    assert door.open is True
    b = Box(game, b.start, b.end, reverb_settings={'gain': 0.5}, door=b.door)
    b.door.open = True
    b.close()
    assert isinstance(b.reverb, GlobalFdnReverb)
    sleep(0.2)
    assert b.reverb.gain == b.reverb_settings['gain']


def test_nearest_door(game: Game, door: Door) -> None:
    """Test Box.nearest_door."""
    room: Box = Box(game, Point(0, 0, 0), Point(3, 3, 3))
    assert room.nearest_door(room.start) is None
    doorstep: Box = Box(game, room.end, room.end, door=door, parent=room)
    assert room.nearest_door(room.start) is None
    assert room.nearest_door(room.start, same_z=False) is doorstep
    doorstep.start.z = room.start.z
    assert room.nearest_door(room.start) is doorstep
    assert room.nearest_door(room.start, same_z=False) is doorstep


def test_nearest_door_with_descendants(game: Game, door: Door) -> None:
    """Test that we can get the nearest door when the door isn't a child."""
    foundation: Box = Box(game, Point(0, 0, 0), Point(5, 5, 5))
    office: Box = Box(game, Point(3, 3, 0), foundation.end, parent=foundation)
    doorstep: Box = Box(
        game, office.start, office.bounds.top_back_left, door=door,
        parent=office, name='Doorstep'
    )
    assert foundation.nearest_door(foundation.start) is doorstep
    assert foundation.nearest_door(Point(0, 0, 1)) is None
    assert foundation.nearest_door(Point(0, 0, 1), same_z=False) is doorstep
    second_door: Box = Box(
        game, foundation.start, foundation.bounds.top_back_left, door=Door(),
        parent=foundation, name='Second Door'
    )
    assert foundation.nearest_door(foundation.start) is second_door
    assert foundation.nearest_door(Point(0, 0, 1)) is None
    assert foundation.nearest_door(Point(0, 0, 1), same_z=False) is second_door
    third_door: Box = Box(
        game, foundation.bounds.bottom_front_right,
        foundation.bounds.top_front_right,
        door=door, name='Third Box', parent=foundation
    )
    assert foundation.nearest_door(foundation.start) is second_door
    assert foundation.nearest_door(third_door.start) is third_door


def test_nearest_portal(game: Game, box_level: BoxLevel) -> None:
    """Test Box.nearest_portal."""
    room: Box = Box(game, Point(0, 0, 0), Point(3, 3, 3))
    assert room.nearest_portal(room.start) is None
    p: Portal = Portal(box_level, Point(0, 0, 0))
    assert room.nearest_portal(room.start) is None
    doorstep: Box = Box(
        game, room.end.copy(), room.end.copy(), portal=p, parent=room
    )
    assert room.nearest_portal(room.start, same_z=False) is doorstep
    doorstep.start.z = room.start.z
    assert room.nearest_portal(room.start) is doorstep
    assert room.nearest_portal(room.start, same_z=False) is doorstep
    second_doorstep: Box = Box(
        game, room.start.copy(), room.bounds.top_back_left.copy(), portal=p,
        parent=room
    )
    assert room.nearest_portal(room.start) is second_doorstep


def test_nearest_portal_with_descendants(game: Game, box: Box) -> None:
    """Test that we can get the nearest door when the door isn't a child."""
    level: BoxLevel = BoxLevel(game, box)
    foundation: Box = Box(game, Point(0, 0, 0), Point(5, 5, 5))
    office: Box = Box(game, Point(3, 3, 0), foundation.end, parent=foundation)
    portal: Box = Box(
        game, office.start, office.start + Point(0, 0, office.end.z),
        portal=Portal(
            level, Point(0, 0, 0)
        ), parent=office
    )
    assert foundation.nearest_portal(foundation.start) is portal
    assert foundation.nearest_portal(Point(0, 0, 1)) is None
    assert foundation.nearest_portal(Point(0, 0, 1), same_z=False) is portal
    second_portal: Box = Box(
        game, foundation.start, Point(0, 0, foundation.end.z), portal=Portal(
            level, Point(0, 0, 0)
        ), parent=foundation
    )
    assert foundation.nearest_portal(foundation.start) is second_portal
    assert foundation.nearest_portal(Point(0, 0, 1)) is None
    assert foundation.nearest_portal(
        Point(0, 0, 1), same_z=False
    ) is second_portal


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


def test_get_oldest_parent(game: Game) -> None:
    """Tes the get_oldest_parent method."""
    start: Point = Point(0, 0, 0)
    end: Point = Point(3, 3, 3)
    a: Box = Box(game, start, end)
    b: Box = Box(game, start, end, parent=a)
    c: Box = Box(game, start, end, parent=b)
    assert a.get_oldest_parent() is a
    assert b.get_oldest_parent() is a
    assert c.get_oldest_parent() is a
    d: Box = Box(game, start, end)
    assert d.get_oldest_parent() is d


def test_get_descendants(game: Game) -> None:
    """Test the get_descendants method."""
    start: Point = Point(0, 0, 0)
    end: Point = Point(5, 5, 5)
    grandparent: Box = Box(game, start, end)
    assert list(grandparent.get_descendants()) == []
    parent: Box = Box(game, start, end, parent=grandparent)
    assert list(grandparent.get_descendants()) == [parent]
    child_1: Box = Box(game, start, end, parent=parent)
    child_2: Box = Box(game, start, end, parent=parent)
    assert list(grandparent.get_descendants()) == [parent, child_1, child_2]


def test_filter_descendants(game: Game) -> None:
    """Test the filter_descendant method."""
    start: Point = Point(0, 0, 0)
    end: Point = Point(5, 5, 5)

    def filter_descendant(descendant: Box) -> bool:
        return descendant.name == 'Child 1'

    grandparent: Box = Box(game, start, end, name='Grandparent')
    assert list(grandparent.filter_descendants(filter_descendant)) == []
    parent: Box = Box(game, start, end, parent=grandparent, name='Parent')
    assert list(grandparent.filter_descendants(filter_descendant)) == []
    child_1: Box = Box(game, start, end, parent=parent, name='Child 1')
    Box(game, start, end, parent=parent, name='Child 2')
    assert list(grandparent.filter_descendants(filter_descendant)) == [child_1]


def test_centre(game: Game) -> None:
    """Test the centre of a box."""
    b: Box = Box(game, Point(1, 1, 1), Point(4, 4, 4))
    assert b.centre == Point(2.5, 2.5, 2.5)
    b = Box(game, Point(0, 0, 0), Point(5, 5, 5))
    assert b.centre == Point(2.5, 2.5, 2.5)
    b = Box(game, Point(3, 4, 5), Point(7, 8, 9))
    assert b.centre == Point(5.0, 6.0, 7.0)


def test_make_sound_manager(game: Game) -> None:
    """Test making a sound manager."""
    b: Box = Box(
        game, Point(0, 0, 0), Point(3, 3, 3), reverb_settings={'gain': 0.2}
    )
    m: SoundManager = b.get_sound_manager()
    assert isinstance(m, SoundManager)
    assert isinstance(m.source, Source3D)
    sleep(0.2)
    assert m.source.position == b.centre.coordinates
    assert m.source.panner_strategy is PannerStrategy.HRTF
    assert b.reverb is None


def test_make_reverb(game: Game, box: Box) -> None:
    """Test the make_reverb method."""
    r: GlobalFdnReverb = box.get_reverb()
    assert isinstance(r, GlobalFdnReverb)
    sleep(0.2)
    assert r.gain == 1.0
    box = Box(
        game, Point(0, 0, 0), Point(3, 3, 3), reverb_settings={'gain': 0.5}
    )
    r = box.get_reverb()
    assert isinstance(r, GlobalFdnReverb)
    sleep(0.2)
    assert r.gain == 0.5


def test_del(game: Game) -> None:
    """Test deleting boxes."""
    b: Box = Box(
        game, Point(0, 0, 0), Point(3, 3, 3), reverb_settings={'gain': 0.2}
    )
    r: GlobalFdnReverb = b.get_reverb()
    b.reverb = r
    assert isinstance(b.reverb, GlobalFdnReverb)
    del b
    with raises(SynthizerError):
        r.destroy()
