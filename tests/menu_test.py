"""Test menus."""

from earwax import Game, Menu, MenuItem, Level, Editor
from earwax.game import OptionalGenerator
from pyglet.window import key


def test_init(game: Game, menu: Menu) -> None:
    assert menu.game is game
    assert menu.items == []
    assert menu.title == 'Test Menu'


def test_add_item(menu: Menu) -> None:
    assert isinstance(menu, Menu)
    i: MenuItem = menu.add_item('Test', print)
    assert isinstance(i, MenuItem)
    assert i.title == 'Test'
    assert i.func is print


def test_yield(game: Game, menu: Menu, level: Level) -> None:
    new_title: str = 'Worked'
    game.push_level(menu)
    game.push_level(level)

    @level.action('Go back', symbol=key.BACKSPACE)
    def go_back() -> OptionalGenerator:
        game.pop_level()
        yield
        menu.title = new_title
    game.on_key_press(key.BACKSPACE, 0)
    game.on_key_release(key.BACKSPACE, 0)
    assert game.level is menu
    assert menu.title == new_title


def test_yield_replaces_menu(
    game: Game, menu: Menu, level: Level, editor: Editor
) -> None:
    game.push_level(menu)
    game.push_level(level)

    @level.action('Window Title', symbol=key.E)
    def push_editor():
        yield
        game.replace_level(editor)

    game.on_key_press(key.E, 0)
    game.on_text('e')
    game.on_key_release(key.E, 0)
    assert game.level is editor
    assert editor.text == ''
