"""Tests the Game class."""

from pyglet.window import key
from pytest import raises

from earwax import Action, Game, Menu


class WorksWithoutYield(Exception):
    pass


class WorksFirstYield(Exception):
    pass


class WorksSecondYield(Exception):
    pass


def test_init(game):
    assert isinstance(game, Game)
    assert game.title == 'Test'
    assert game.actions == []
    assert game.triggered_actions == []
    assert game.on_key_release_generators == {}
    assert game.window is None
    assert game.menus == []
    assert game.editor is None


def test_action(game):
    a = game.action('Print')(print)
    assert isinstance(a, Action)
    assert a.title == 'Print'
    assert a.game is game
    assert a.func is print
    assert a.symbol is None
    assert a.modifiers == 0
    assert a.interval is None
    assert a.can_run == game.normal
    assert a.last_run == 0.0
    assert game.actions == [a]


def test_on_key_press(game):
    @game.action('Test without yield', symbol=key.T)
    def test_without_yield():
        raise WorksWithoutYield()

    with raises(WorksWithoutYield):
        game.on_key_press(key.T, 0)
    game.on_key_press(key.T, key.MOD_SHIFT)
    game.on_key_press(key.P, 0)
    game.on_key_press(key.P, key.MOD_SHIFT)

    @game.action('First yield', symbol=key._1)
    def first_yield():
        raise WorksFirstYield()
        yield

    with raises(WorksFirstYield):
        game.on_key_press(key._1, 0)


def test_on_key_release(game):
    @game.action('Second yield', symbol=key._2)
    def second_yield():
        yield
        raise WorksSecondYield()

    game.on_key_press(key._2, 0)
    with raises(WorksSecondYield):
        game.on_key_release(key._2, 0)


def test_push_menu(game, menu):
    game.push_menu(menu)
    assert game.menus == [menu]
    m = Menu('Second Menu')
    game.push_menu(m)
    assert game.menus == [menu, m]


def test_replace_menu(game, menu):
    game.push_menu(menu)
    m = Menu('Second Menu')
    game.replace_menu(m)
    assert game.menus == [m]
    game.push_menu(menu)
    m2 = Menu('Third Menu')
    game.replace_menu(m2)
    assert game.menus == [m, m2]


def test_pop_menu(game, menu):
    game.push_menu(menu)
    game.pop_menu()
    assert game.menus == []
    game.push_menu(menu)
    m = Menu('Second Menu')
    game.push_menu(m)
    assert game.menus == [menu, m]
    game.pop_menu()
    assert game.menus == [menu]
    game.push_menu(m)
    game.push_menu(menu)
    game.clear_menus()
    assert game.menus == []


def test_no_menu(game, menu):
    assert game.no_menu() is True
    game.push_menu(menu)
    assert game.no_menu() is False


def test_no_editor(game, editor):
    assert game.no_editor() is True
    game.editor = editor
    assert game.no_editor() is False


def test_normal(game, editor, menu):
    assert game.normal() is True
    game.editor = editor
    assert game.normal() is False
    game.editor = None
    assert game.normal() is True
    game.push_menu(menu)
    assert game.normal() is False
    game.pop_menu()
    assert game.normal() is True


def test_menu(game, menu):
    assert game.menu is None
    game.push_menu(menu)
    assert game.menu is menu
    m = Menu('Second Menu')
    game.push_menu(m)
    assert game.menu is m
    game.replace_menu(menu)
    assert game.menu is menu


def test_add_menu_actions(game):
    game.add_menu_actions()
    assert game.actions[0].func == game.menu_activate
    assert game.actions[1].func == game.dismiss
    assert game.actions[2].func == game.menu_down
    assert game.actions[3].func == game.menu_up
