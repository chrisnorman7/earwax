"""Test the Action class and all related functions."""

from inspect import isgenerator

from pyglet.window import key, mouse
from pytest import raises

from earwax import Action, Game, Level


class Works(Exception):
    """A test worked."""


class LeftMouseButton(Exception):
    """Left mouse button was pressed."""


class RightMouseButton(Exception):
    """The right mouse button was pressed."""


def test_init() -> None:
    """Test that instances actions properly."""
    a = Action('Print', print)
    assert a.title == 'Print'
    assert a.func is print
    assert a.symbol is None
    assert a.modifiers == 0
    a = Action('Print', print, symbol=key.P, modifiers=key.MOD_SHIFT)
    assert a.symbol == key.P
    assert a.modifiers == key.MOD_SHIFT


def test_mouse(game: Game, level: Level) -> None:
    """Test actions with mouse buttons."""

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


def test_mouse_generator(game: Game, level: Level) -> None:
    """Test actions with mouse button triggers that yield."""
    game.push_level(level)

    @level.action('Mouse button', mouse_button=mouse.LEFT)
    def mouse_button():
        yield
        raise Works()

    game.on_mouse_press(0, 0, mouse.LEFT, 0)
    assert isgenerator(game.mouse_release_generators[mouse.LEFT])
    with raises(Works):
        game.on_mouse_release(0, 0, mouse.LEFT, 0)
