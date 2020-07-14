"""Test the Action class, and all related functions."""

from pyglet.window import key

from earwax import Action, Game


def test_init():
    g = Game('Test')
    a = Action(g, 'Print', print)
    assert a.game is g
    assert a.title == 'Print'
    assert a.func is print
    assert a.symbol is None
    assert a.modifiers == 0
    assert a.can_run == g.normal
    a = Action(g, 'Print', print, symbol=key.P, modifiers=key.MOD_SHIFT)
    assert a.symbol == key.P
    assert a.modifiers == key.MOD_SHIFT
