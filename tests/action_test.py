"""Test the Action class, and all related functions."""

from pytest import raises
from pyglet.window import key, mouse

from earwax import Action, Game, Level


class LeftMouseButton(Exception):
    pass


class RightMouseButton(Exception):
    pass


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


def test_mouse(game: Game, level: Level) -> None:

    @level.action('Left mouse button', mouse_button=mouse.LEFT)
    def left_mouse():
        raise LeftMouseButton()

    @level.action('Right mouse button', mouse_button=mouse.RIGHT)
    def right_mouse():
        raise RightMouseButton()

    game.push_level(level)
    game.click_mouse(mouse.MIDDLE, 0)
    with raises(LeftMouseButton):
        game.click_mouse(mouse.LEFT, 0)
    with raises(RightMouseButton):
        game.click_mouse(mouse.RIGHT, 0)
