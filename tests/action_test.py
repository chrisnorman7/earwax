"""Test the Action class, and all related functions."""

from pyglet.window import key

from earwax import Action, Level


def test_init(level: Level) -> None:
    a = Action(level, 'Print', print)
    assert a.level is level
    assert a.title == 'Print'
    assert a.func is print
    assert a.symbol is None
    assert a.modifiers == 0
    a = Action(level, 'Print', print, symbol=key.P, modifiers=key.MOD_SHIFT)
    assert a.symbol == key.P
    assert a.modifiers == key.MOD_SHIFT
