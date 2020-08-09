"""Test menus."""

from earwax import Game, Menu, MenuItem


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
