"""Test the earwax.Die class."""

from pytest import raises

from earwax import Die


class OnRollWorks(Exception):
    """Rolling worked."""


def test_init() -> None:
    """Test initialisation."""
    d: Die = Die()
    assert d.sides == 6
    d = Die(4)
    assert d.sides == 4


def test_roll() -> None:
    """Test die rolling."""
    d: Die = Die()
    assert isinstance(d.roll(), int)


def test_on_roll() -> None:
    """Test the on_roll event."""
    d: Die = Die()

    @d.event
    def on_roll(value: int) -> None:
        raise OnRollWorks(value)

    with raises(OnRollWorks) as exc:
        d.roll()
    assert isinstance(exc.value.args[0], int)
