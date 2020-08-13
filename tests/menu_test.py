"""Test menus."""

from pyglet.window import key

from earwax import ActionMenu, Editor, Game, Level, Menu, MenuItem
from earwax.game import OptionalGenerator


class Works(Exception):
    pass


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
    game.press_key(key.BACKSPACE, 0, motion=key.MOTION_BACKSPACE)
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

    game.press_key(key.E, 0, string='e')
    assert game.level is editor
    assert editor.text == ''


def test_action_menu(game: Game, level: Level, menu: Menu) -> None:
    game.push_level(level)
    a: ActionMenu = ActionMenu('Actions', game)
    assert a.items == []
    assert a.position == -1

    @level.action('Menu', symbol=key.M)
    def get_menu() -> OptionalGenerator:
        yield
        game.push_level(menu)

    @level.action('Actions', symbol=key.A)
    def actions():
        yield  # So that the a key doesn't change focus in the actions menu.
        game.push_level(ActionMenu('Actions', game))

    game.press_key(key.A, 0, string='a')
    assert isinstance(game.level, ActionMenu)
    a = game.level
    assert a.title == 'Actions'
    assert len(a.items) == 2
    assert a.items[0].title == 'Menu [M]'
    assert a.items[1].title == 'Actions [A]'
    assert a.position == -1
    assert game.level is a
    assert game.levels == [level, a]
    game.press_key(key.DOWN, 0, motion=key.MOTION_DOWN)
    assert a.position == 0
    game.press_key(key.RETURN, 0, string='\n')
    assert game.levels == [level, menu]
    assert game.level is menu
