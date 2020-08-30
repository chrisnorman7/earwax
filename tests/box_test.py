from pytest import raises

from earwax import Box, OutOfBounds, Point


def test_init() -> None:
    b: Box = Box(Point(0, 0), Point(3, 3))
    assert b.bottom_left == Point(0, 0)
    assert b.top_right == Point(3, 3)
    b = Box(Point(5, 5))
    assert b.bottom_left == Point(5, 5)
    assert b.top_right == Point(5, 5)
    assert b.top_right is not b.bottom_left


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
    gc: Box = Box(Point(1, 1))
    c.add_child(gc)
    assert gc.parent is c
    assert c.children == [gc]
    broken: Box = Box(Point(-1, 0))
    with raises(OutOfBounds) as exc:
        b.add_child(broken)
    assert exc.value.args == (b, broken)
    broken = Box(Point(10, 10))
    with raises(OutOfBounds) as exc:
        b.add_child(broken)
    assert exc.value.args == (b, broken)
