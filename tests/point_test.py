from pytest import raises

from earwax import Point


def test_init() -> None:
    p = Point(0, 0)
    assert p.x == 0
    assert p.y == 0


def test_add() -> None:
    p = Point(3, 2)
    p += 3
    assert p.x == 6
    assert p.y == 5
    p += Point(1, 3)
    assert p.x == 7
    assert p.y == 8
    with raises(TypeError):
        p += 'Failure.'  # type: ignore[operator]


def test_subtract() -> None:
    p = Point(10, 12)
    p -= 3
    assert p.x == 7
    assert p.y == 9
    p -= Point(1, 4)
    assert p.x == 6
    assert p.y == 5
    with raises(TypeError):
        p -= 'Failure.'  # type: ignore[operator]


def test_multiply() -> None:
    p = Point(8, 9)
    p *= 10
    assert p.x == 80
    assert p.y == 90
    p *= Point(2, 3)
    assert p.x == 160
    assert p.y == 270
    with raises(TypeError):
        p *= 'Failure.'  # type: ignore[operator]


def test_lessthan() -> None:
    assert Point(1, 1) < Point(3, 3)
    assert not Point(4, 4) < Point(2, 1)
    assert not Point(55, 2) < Point(3, 3)


def test_greaterthan() -> None:
    assert Point(4, 4) > Point(2, 1)
    assert not Point(1, 1) > Point(3, 3)
    assert not Point(4, 1) > Point(2, 2)


def test_copy() -> None:
    p: Point = Point(5, 4)
    copy: Point = p.copy()
    assert p == copy
    assert copy is not p
