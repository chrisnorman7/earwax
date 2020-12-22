"""Provides tests for the Portal class."""

from pytest import raises

from earwax import BoxLevel, Point, Portal


class EnterWorks(Exception):
    """The enter key worked."""


class ExitWorks(Exception):
    """Exiting worked."""


def test_init(box_level: BoxLevel) -> None:
    """Test initialization."""
    p: Portal = Portal(box_level, Point(3, 3, 3))
    assert p.level is box_level
    assert p.coordinates == Point(3, 3, 3)
    assert p.bearing is None
    assert p.enter_sound is None
    assert p.exit_sound is None


def test_on_enter(box_level: BoxLevel) -> None:
    """Test the on_enter event."""
    p: Portal = Portal(box_level, Point(1, 1, 1))

    @p.event
    def on_enter() -> None:
        raise EnterWorks

    with raises(EnterWorks):
        p.dispatch_event('on_enter')


def test_on_exit(box_level: BoxLevel) -> None:
    """Test the on_exit event."""
    p: Portal = Portal(box_level, Point(3, 3, 3))

    @p.event
    def on_exit() -> None:
        raise ExitWorks()

    with raises(ExitWorks):
        p.dispatch_event('on_exit')
