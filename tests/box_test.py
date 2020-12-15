"""Test the Box class."""

from typing import List

from pytest import raises

from earwax import (Box, BoxBounds, BoxLevel, Door, FittedBox, NotADoor,
                    OutOfBounds, Point, Portal, box_row)


def test_init() -> None:
    """Test that boxes initialise properly."""
    b: Box = Box(Point(0, 0, 0), Point(3, 3, 0))
    assert b.start == Point(0, 0, 0)
    assert b.end == Point(3, 3, 0)
    assert b.surface_sound is None
    c: Box = Box(b.start, b.end, parent=b)
    assert c.parent is b
    assert c in b.children


def test_add_child() -> None:
    """Test adding child boxes."""
    b: Box = Box(Point(0, 0, 0), Point(3, 3, 0))
    c: Box = Box(Point(1, 1, 0), Point(1, 1, 0), parent=b)
    assert c.parent is b
    assert b.children == [c]
    gc: Box = Box(Point(1, 1, 0), Point(1, 1, 0), parent=c)
    assert gc.parent is c
    assert c.children == [gc]
    broken: Box = Box(Point(-1, 0, 5), Point(-1, 0, -2))
    with raises(OutOfBounds) as exc:
        b.add_child(broken)
    assert exc.value.args == (b, broken)
    broken = Box(Point(10, 10, 10), Point(10, 10, 10))
    with raises(OutOfBounds) as exc:
        b.add_child(broken)
    assert exc.value.args == (b, broken)


def test_contains_point() -> None:
    """Test Box.contains_point."""
    b: Box = Box(Point(0, 0, 0), Point(0, 0, 0))
    assert b.contains_point(Point(0, 0, 0))
    b.end = Point(5, 5, 0)
    assert b.contains_point(Point(3, 3, 0))
    assert not b.contains_point(Point(55, 54, 52))
    assert not b.contains_point(Point(-3, -4, 0))
    assert not b.contains_point(Point(-1, 4, 5))
    assert not b.contains_point(Point(3, 7, 2))


def test_get_containing_child() -> None:
    """Test Box.get_containing_box."""
    parent: Box = Box(Point(0, 0, 0), Point(100, 100, 5))
    # Draw 2 parallel lines, like train tracks.
    southern_rail: Box = Box(Point(0, 0, 0), Point(100, 0, 0), parent=parent)
    northern_rail = Box(Point(0, 2, 0), Point(100, 2, 0), parent=parent)
    assert parent.get_containing_box(Point(5, 5, 0)) is parent
    assert parent.get_containing_box(Point(0, 0, 0)) is southern_rail
    assert parent.get_containing_box(Point(3, 2, 0)) is northern_rail
    assert parent.get_containing_box(Point(200, 201, 0)) is None


def test_fitted_box() -> None:
    """Test the FittedBox class."""
    southwest_box: Box = Box(Point(3, 5, 0), Point(8, 2, 0))
    northeast_box: Box = Box(Point(32, 33, 0), Point(80, 85, 5))
    middle_box: Box = Box(Point(14, 15, 2), Point(18, 22, 2))
    box: FittedBox = FittedBox([middle_box, northeast_box, southwest_box])
    assert box.start == southwest_box.start
    assert box.end == northeast_box.end


def test_row() -> None:
    """Test the box_row function."""
    start: Point = Point(1, 1, 0)
    boxes: List[Box] = box_row(start, Point(5, 5, 1), 3, Point(1, 0, 0))
    assert len(boxes) == 3
    first: Box
    second: Box
    third: Box
    first, second, third = boxes
    assert first.start == start
    assert first.end == Point(5, 5, 0)
    assert second.start == Point(6, 1, 0)
    assert second.end == Point(10, 5, 0)
    assert third.start == Point(11, 1, 0)
    assert third.end == Point(15, 5, 0)
    first, second, third = box_row(
        Point(0, 0, 0), Point(3, 4, 1), 3, Point(0, 3, 0)
    )
    assert first.start == Point(0, 0, 0)
    assert first.end == Point(2, 3, 0)
    assert second.start == Point(0, 6, 0)
    assert second.end == Point(2, 9, 0)
    assert third.start == Point(0, 12, 0)
    assert third.end == Point(2, 15, 0)
    first, second, third = box_row(start, Point(5, 5, 1), 3, Point(0, 0, 1))
    assert first.start == start
    assert first.end == Point(5, 5, 0)
    assert second.start == Point(1, 1, 1)
    assert second.end == Point(5, 5, 1)
    assert third.start == Point(1, 1, 2)
    assert third.end == Point(5, 5, 2)


def test_open() -> None:
    """Test door opening."""
    b: Box = Box(Point(0, 0, 0), Point(0, 0, 0))

    @b.event
    def on_close() -> None:
        raise RuntimeError('This event should not have fired.')

    with raises(NotADoor):
        b.open(None)
    d = Door(open=False)
    b.door = d
    b.open(None)
    assert d.open is True

    @b.event
    def on_open() -> None:
        d.open = False

    b.open(None)
    assert d.open is False


def test_close() -> None:
    """Test closing doors."""
    b: Box = Box(Point(0, 0, 0), Point(0, 0, 0))

    @b.event
    def on_open() -> None:
        raise RuntimeError('This event should not have fired.')

    with raises(NotADoor):
        b.close(None)
    d = Door(open=True)
    b.door = d
    b.close(None)
    assert d.open is False

    @b.event
    def on_close() -> None:
        d.open = True

    b.close(None)

    assert d.open is True


def test_nearest_door() -> None:
    """Test Box.nearest_door."""
    room: Box = Box(Point(0, 0, 0), Point(3, 3, 3))
    assert room.nearest_door() is None
    d = Door()
    doorstep: Box = Box(room.end, room.end, door=d, parent=room)
    assert room.nearest_door() is None
    assert room.nearest_door(same_z=False) is doorstep
    doorstep.start.z = room.start.z
    assert room.nearest_door() is doorstep
    assert room.nearest_door(same_z=False) is doorstep


def test_nearest_portal(box_level: BoxLevel) -> None:
    """Test Box.nearest_portal."""
    room: Box = Box(Point(0, 0, 0), Point(3, 3, 3))
    assert room.nearest_portal() is None
    p: Portal = Portal(box_level, Point(0, 0, 0))
    doorstep: Box = Box(room.end, room.end, portal=p, parent=room)
    assert room.nearest_portal() is None
    assert room.nearest_portal(same_z=False) is doorstep
    doorstep.start.z = room.start.z
    assert room.nearest_portal() is doorstep
    assert room.nearest_portal(same_z=False) is doorstep


def test_bounds() -> None:
    """Test the bounds of a box."""
    box: Box = Box(Point(1, 2, 3), Point(4, 5, 6))
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


def test_width() -> None:
    """Test box.width."""
    b: BoxBounds = Box(Point(0, 1, 2), Point(5, 4, 3)).bounds
    assert b.width == 5


def test_depth() -> None:
    """Test box depth."""
    b: BoxBounds = Box(Point(0, 1, 2), Point(5, 4, 3)).bounds
    assert b.depth == 3


def test_height() -> None:
    """Test box height."""
    b: BoxBounds = Box(Point(0, 1, 2), Point(5, 4, 3)).bounds
    assert b.height == 1


def test_area() -> None:
    """Test box area."""
    b: BoxBounds = Box(Point(0, 0, 0), Point(5, 5, 5)).bounds
    assert b.area == 25
    b = Box(Point(5, 6, 0), Point(9, 12, 7)).bounds
    assert b.area == 24


def test_volume() -> None:
    """Test box volume."""
    b: BoxBounds = Box(Point(1, 2, 3), Point(10, 9, 8)).bounds
    assert b.volume == 315
