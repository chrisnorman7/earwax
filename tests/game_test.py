"""Tests the Game class."""

from pyglet.window import key
from pytest import raises

from earwax import Game, Level, Menu


class WorksWithoutYield(Exception):
    pass


class WorksFirstYield(Exception):
    pass


class WorksSecondYield(Exception):
    pass


def test_init(game: Game) -> None:
    assert isinstance(game, Game)
    assert game.levels == []
    assert game.window is None


def test_on_key_press(game: Game, level: Level) -> None:
    game.push_level(level)

    @level.action('Test without yield', symbol=key.T)
    def test_without_yield():
        raise WorksWithoutYield()

    with raises(WorksWithoutYield):
        game.on_key_press(key.T, 0)
    game.on_key_press(key.T, key.MOD_SHIFT)
    game.on_key_press(key.P, 0)
    game.on_key_press(key.P, key.MOD_SHIFT)

    @level.action('First yield', symbol=key._1)
    def first_yield():
        raise WorksFirstYield()
        yield

    with raises(WorksFirstYield):
        game.on_key_press(key._1, 0)


def test_on_key_release(game: Game, level: Level) -> None:
    game.push_level(level)

    @level.action('Second yield', symbol=key._2)
    def second_yield():
        yield
        raise WorksSecondYield()

    game.on_key_press(key._2, 0)
    with raises(WorksSecondYield):
        game.on_key_release(key._2, 0)


def test_push_level(game: Game, level: Level) -> None:
    game.push_level(level)
    assert game.levels == [level]
    level_2 = Level(game)
    game.push_level(level_2)
    assert game.levels == [level, level_2]


def test_replace_level(game: Game, level: Level, menu: Menu) -> None:
    game.push_level(level)
    assert game.levels == [level]
    game.replace_level(menu)
    assert game.levels == [menu]
    game.push_level(level)
    assert game.levels == [menu, level]
    m2 = Menu(game, 'Second Menu')
    game.replace_level(m2)
    assert game.levels == [menu, m2]


def test_pop_level(game: Game, level: Level, menu: Menu) -> None:
    game.push_level(level)
    assert game.levels == [level]
    game.pop_level()
    assert game.levels == []
    game.push_level(level)
    assert game.levels == [level]
    game.push_level(menu)
    assert game.levels == [level, menu]
    game.pop_level()
    assert game.levels == [level]


def test_clear_levels(game: Game, level: Level, menu: Menu) -> None:
    assert game.levels == []
    game.clear_levels()
    assert game.levels == []
    game.push_level(level)
    game.push_level(menu)
    assert game.levels == [level, menu]
    game.clear_levels()
    assert game.levels == []


def test_level(game: Game, level: Level, menu: Menu) -> None:
    assert game.level is None
    game.push_level(level)
    assert game.level is level
    game.push_level(menu)
    assert game.level is menu
    game.pop_level()
    assert game.level is level
    game.clear_levels()
    game.push_level(menu)
    assert game.level is menu
