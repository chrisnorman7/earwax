"""Tests for the Point class."""

from earwax import Point
from movement_2d import coordinates_in_direction
from pytest import raises


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
        p += "Failure."  # type: ignore[operator]


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
        p -= "Failure."  # type: ignore[operator]


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
        p *= "Failure."  # type: ignore[operator]


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


def test_angle_between() -> None:
    """Test getting the angle between two points."""
    a: Point = Point(0, 0, 0)
    b: Point = Point(0, 1, 0)
    assert a.angle_between(b) == 0
    assert b.angle_between(a) == 180
    b = Point(1, 0, 0)
    assert a.angle_between(b) == 90
    assert b.angle_between(a) == 270
    a = Point(1, 1, 3)
    b = Point(3, 3, 6)
    assert a.angle_between(b) == 45
    assert b.angle_between(a) == 225


def test_in_direction() -> None:
    """Test getting coordinates in a direction."""
    a: Point = Point(1, 1, 1)
    b: Point = a.in_direction(180)
    x: float
    y: float
    x, y = coordinates_in_direction(a.x, a.y, 180)
    assert isinstance(b, Point)
    assert b.x == x
    assert b.y == y
    assert b.z == a.z


def test_origin() -> None:
    """Test the origin constructor."""
    p: Point = Point.origin()
    assert p == Point(0, 0, 0)


def test_random() -> None:
    """Test the random constructor."""
    assert Point.random(Point.origin(), Point.origin()) == Point.origin()
    a: Point[int] = Point(1, 2, 3)
    b: Point[int] = Point(4, 5, 6)
    p: Point[int] = Point.random(a, b)
    assert p.x <= b.x and p.x >= a.x
    assert p.y <= b.y and p.y >= a.y
    assert p.z <= b.z and p.z >= a.z
