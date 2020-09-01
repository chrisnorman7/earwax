from typing import List

from pytest import raises

from earwax import Box, FittedBox, OutOfBounds, Point, box_row


def test_init() -> None:
    b: Box = Box(Point(0, 0), Point(3, 3))
    assert b.bottom_left == Point(0, 0)
    assert b.top_right == Point(3, 3)
    assert b.surface_sound is None
    c: Box = Box(b.bottom_left, b.top_right, parent=b)
    assert c.parent is b
    assert c in b.children


def test_corners() -> None:
    b: Box = Box(Point(3, 4), Point(6, 7))
    assert b.bottom_right == Point(6, 4)
    assert b.top_left == Point(3, 7)


def test_add_child() -> None:
    b: Box = Box(Point(0, 0), Point(3, 3))
    c: Box = Box(Point(1, 1), Point(1, 1))
    b.add_child(c)
    assert c.parent is b
    assert b.children == [c]
    gc: Box = Box(Point(1, 1), Point(1, 1))
    c.add_child(gc)
    assert gc.parent is c
    assert c.children == [gc]
    broken: Box = Box(Point(-1, 0), Point(-1, 0))
    with raises(OutOfBounds) as exc:
        b.add_child(broken)
    assert exc.value.args == (b, broken)
    broken = Box(Point(10, 10), Point(10, 10))
    with raises(OutOfBounds) as exc:
        b.add_child(broken)
    assert exc.value.args == (b, broken)


def test_contains_point() -> None:
    b: Box = Box(Point(0, 0), Point(0, 0))
    assert b.contains_point(Point(0, 0))
    b.top_right = Point(5, 5)
    assert b.contains_point(Point(3, 3))
    assert not b.contains_point(Point(55, 54))
    assert not b.contains_point(Point(-3, -4))
    assert not b.contains_point(Point(-1, 4))
    assert not b.contains_point(Point(3, 7))


def test_get_containing_child() -> None:
    parent: Box = Box(Point(0, 0), Point(100, 100))
    # Draw 2 parallel lines, like train tracks.
    southern_rail: Box = Box(Point(0, 0), Point(100, 0), parent=parent)
    northern_rail = Box(Point(0, 2), Point(100, 2), parent=parent)
    assert parent.get_containing_box(Point(5, 5)) is parent
    assert parent.get_containing_box(Point(0, 0)) is southern_rail
    assert parent.get_containing_box(Point(3, 2)) is northern_rail
    assert parent.get_containing_box(Point(200, 201)) is None


def test_fitted_box() -> None:
    southwest_box: Box = Box(Point(3, 5), Point(8, 2))
    northeast_box: Box = Box(Point(32, 33), Point(80, 85))
    middle_box: Box = Box(Point(14, 15), Point(18, 22))
    box: FittedBox = FittedBox([middle_box, northeast_box, southwest_box])
    assert box.bottom_left == southwest_box.bottom_left
    assert box.top_right == northeast_box.top_right


def test_row() -> None:
    start: Point = Point(1, 1)
    boxes: List[Box] = box_row(start, 5, 5, 3, 1, 0)
    assert len(boxes) == 3
    first: Box
    second: Box
    third: Box
    first, second, third = boxes
    assert first.bottom_left == start
    assert first.top_right == Point(5, 5)
    assert second.bottom_left == Point(6, 1)
    assert second.top_right == Point(10, 5)
    assert third.bottom_left == Point(11, 1)
    assert third.top_right == Point(15, 5)
    first, second, third = box_row(Point(0, 0), 3, 4, 3, 0, 3)
    assert first.bottom_left == Point(0, 0)
    assert first.top_right == Point(2, 3)
    assert second.bottom_left == Point(0, 6)
    assert second.top_right == Point(2, 9)
    assert third.bottom_left == Point(0, 12)
    assert third.top_right == Point(2, 15)
