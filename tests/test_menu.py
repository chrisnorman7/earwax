"""Test menus."""

from pyglet.window import key

from earwax import ActionMenu, Editor, Game, Level, Menu, MenuItem
from earwax.types import OptionalGenerator


class Works(Exception):
    """Something worked."""


def test_init(game: Game, menu: Menu) -> None:
    """Test initialisation."""
    assert menu.game is game
    assert menu.items == []
    assert menu.title == 'Test Menu'


def test_add_item(menu: Menu) -> None:
    """Test the add_item method."""
    assert isinstance(menu, Menu)
    i: MenuItem = menu.add_item(print, title='Test')
    assert isinstance(i, MenuItem)
    assert i.title == 'Test'
    assert i.func is print


def test_yield(game: Game, menu: Menu, level: Level) -> None:
    """Ensure a menu title can be set after yielding."""
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
    """Ensure a menu can be replaced after yielding."""
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
    """Test the ActionMenu class."""
    game.push_level(level)
    a: ActionMenu = ActionMenu(game, 'Actions')
    assert a.items == []
    assert a.position == -1

    @level.action('Menu', symbol=key.M)
    def get_menu() -> OptionalGenerator:
        yield
        game.push_level(menu)

    @level.action('Actions', symbol=key.A)
    def actions():
        yield  # So that the a key doesn't change focus in the actions menu.
        game.push_level(ActionMenu(game, 'Actions'))

    game.press_key(key.A, 0, string='a')
    assert isinstance(game.level, ActionMenu)
    a = game.level
    assert a.title == 'Actions'
    assert len(a.items) == 2
    assert a.items[0].title == get_menu.title
    assert a.items[1].title == actions.title
    assert a.position == -1
    assert game.level is a
    assert game.levels == [level, a]
    game.press_key(key.DOWN, 0, motion=key.MOTION_DOWN)
    # We should now be focussed on the first item in the menu.
    assert a.position == 0
    # When we activate the menu item, we are put into a further menu, which is
    # the list of triggers for the selected action.
    game.press_key(key.RETURN, 0, string='\n')
    assert len(game.levels) == 3
    assert game.level is not menu
    game.press_key(key.DOWN, 0, motion=key.MOTION_DOWN)
    game.press_key(key.RETURN, 0, string='\n')
    assert game.levels == [level, menu]
    assert game.level is menu


def test_add_submenu(game: Game) -> None:
    """Test adding a submenu."""
    m: Menu = Menu(game, 'First menu')
    sm: Menu = Menu(game, 'Second Menu')
    mi: MenuItem = m.add_submenu(sm, False, title='Submenu')
    assert isinstance(mi, MenuItem)
    assert mi.title == 'Submenu'
    game.push_level(m)
    m.move_down()
    assert m.current_item is mi
    assert game.level is m
    game.press_key(key.RETURN, 0)
    assert game.level is sm
    assert game.levels == [m, sm]
    m.add_submenu(sm, True, title='Replace the menu')
    game.pop_level()
    assert game.levels == [m]
    m.move_down()
    game.press_key(key.RETURN, 0)
    assert game.levels == [sm]
