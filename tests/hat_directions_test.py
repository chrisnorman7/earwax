"""Test hat directions."""

from earwax.hat_directions import DEFAULT, DOWN, LEFT, RIGHT, UP


def test_default() -> None:
    """Test default position."""
    assert DEFAULT == (0, 0)


def test_up() -> None:
    """Test up position."""
    assert UP == (0, 1)


def test_down() -> None:
    """Test the down position."""
    assert DOWN == (0, -1)


def test_left() -> None:
    """Test the left position."""
    assert LEFT == (-1, 0)


def test_right() -> None:
    """Test the right position."""
    assert RIGHT == (1, 0)
