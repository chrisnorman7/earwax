"""Tests for the Point class."""

from pytest import raises

from earwax import Point


def test_init() -> None:
    """Test initialisation."""
    p = Point(0, 1, 2)
    assert p.x == 0
    assert p.y == 1
    assert p.z == 2


def test_add() -> None:
    """Test point addition."""
    p = Point(3, 2, 1)
    p += 3
    assert p.x == 6
    assert p.y == 5
    assert p.z == 4
    p += Point(1, 3, 2)
    assert p.x == 7
    assert p.y == 8
    assert p.z == 6
    with raises(TypeError):
        p += 'Failure.'  # type: ignore[operator]


def test_subtract() -> None:
    """Test point subtraction."""
    p = Point(10, 12, 14)
    p -= 3
    assert p.x == 7
    assert p.y == 9
    assert p.z == 11
    p -= Point(1, 4, 2)
    assert p.x == 6
    assert p.y == 5
    assert p.z == 9
    with raises(TypeError):
        p -= 'Failure.'  # type: ignore[operator]


def test_multiply() -> None:
    """Test point multiplication."""
    p = Point(8, 9, 10)
    p *= 10
    assert p.x == 80
    assert p.y == 90
    assert p.z == 100
    p *= Point(2, 3, 4)
    assert p.x == 160
    assert p.y == 270
    assert p.z == 400
    with raises(TypeError):
        p *= 'Failure.'  # type: ignore[operator]


def test_lessthan() -> None:
    """Test Point < Point."""
    assert Point(1, 1, 1) < Point(3, 3, 3)
    assert not Point(4, 4, 4) < Point(2, 1, 0)
    assert not Point(55, 2, 0) < Point(3, 3, 3)
    assert not Point(1, 2, 3) < Point(0, 0, 15)


def test_greaterthan() -> None:
    """Test Point > Point."""
    assert Point(4, 4, 4) > Point(2, 1, 0)
    assert not Point(1, 1, 1) > Point(3, 3, 3)
    assert not Point(4, 1, 1) > Point(2, 2, 2)
    assert not Point(1, 4, 1) > Point(2, 1, 2)
    assert not Point(1, 1, 4) > Point(4, 4, 1)


def test_copy() -> None:
    """Test point copying."""
    p: Point = Point(5, 4, 3)
    copy: Point = p.copy()
    assert p == copy
    assert copy is not p


def test_floor() -> None:
    """Test flooring points."""
    p: Point = Point(1.9, 2.8, 3.7)
    assert p.floor() == Point(1, 2, 3)


def test_coords() -> None:
    """Test Point.coordinates."""
    p: Point = Point(3, 4, 5)
    assert p.coordinates == (3, 4, 5)
    p.x = 6
    p.y = 5
    p.z = 4
    assert p.coordinates == (6, 5, 4)


def test_neg() -> None:
    """Test multiplying Point instances by -1."""
    p: Point = Point(4, 5, 6)
    assert -p == Point(-4, -5, -6)


def test_distance() -> None:
    """Test getting the distance between two points."""
    a: Point = Point(0, 0, 0)
    b = a.copy()
    assert a.distance_between(b) == 0.0
    a = Point(1, 1, 1)
    b = Point(1, 1, 3)
    assert a.distance_between(b) == 2
