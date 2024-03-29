"""Tests the Game class."""

from concurrent.futures.thread import ThreadPoolExecutor
from pathlib import Path
from time import sleep

from pyglet.clock import schedule_once
from pyglet.resource import get_settings_path
from pyglet.window import Window, key
from pytest import raises
from synthizer import Context

from earwax import (ActionMenu, Credit, Game, GameNotRunning, InputModes,
                    Level, Menu, SoundManager)


class PretendDevice:
    """A pretend device."""

    name: str = "Pretend Device"


class PretendJoystick:
    """A pretend joystick object."""

    device: PretendDevice = PretendDevice()


class WorksWithoutYield(Exception):
    """A menu item that doesn't yield worked."""


class WorksFirstYield(Exception):
    """Works after the first yield."""


class WorksSecondYield(Exception):
    """Works after the second yield."""


class BeforeRunWorks(Exception):
    """The before_run event worked."""


class AfterRunWorks(Exception):
    """The after_run event worked."""


def test_init(game: Game) -> None:
    """Test initialisation."""
    assert isinstance(game, Game)
    assert game.levels == []
    assert game.window is None
    assert game.triggered_actions == []
    assert game.key_release_generators == {}
    assert game.event_matchers == {}
    assert game.joysticks == []
    assert isinstance(game.thread_pool, ThreadPoolExecutor)
    assert game.tasks == []
    assert game.credits == []


def test_on_key_press(game: Game, level: Level) -> None:
    """Test pressing keys."""
    game.push_level(level)

    @level.action("Test without yield", symbol=key.T)
    def test_without_yield():
        raise WorksWithoutYield()

    with raises(WorksWithoutYield):
        game.press_key(key.T, 0, string="t")
    game.press_key(key.T, key.MOD_SHIFT, string="T")
    game.press_key(key.P, 0, string="p")
    game.press_key(key.P, key.MOD_SHIFT, string="P")

    @level.action("First yield", symbol=key._1)
    def first_yield():
        raise WorksFirstYield()
        yield

    with raises(WorksFirstYield):
        game.press_key(key._1, 0, string="1")


def test_on_key_release(game: Game, level: Level) -> None:
    """Test the on_key_press event."""
    game.push_level(level)

    @level.action("Second yield", symbol=key._2)
    def second_yield():
        yield
        raise WorksSecondYield()

    game.dispatch_event("on_key_press", key._2, 0)
    with raises(WorksSecondYield):
        game.dispatch_event("on_key_release", key._2, 0)


def test_push_level(game: Game, level: Level) -> None:
    """Test the push_level method."""
    game.push_level(level)
    assert game.levels == [level]
    level_2 = Level(game)
    game.push_level(level_2)
    assert game.levels == [level, level_2]


def test_replace_level(game: Game, level: Level, menu: Menu) -> None:
    """Test the replace_level method."""
    game.push_level(level)
    assert game.levels == [level]
    game.replace_level(menu)
    assert game.levels == [menu]
    game.push_level(level)
    assert game.levels == [menu, level]
    m2 = Menu(game, "Second Menu")
    game.replace_level(m2)
    assert game.levels == [menu, m2]


def test_pop_level(game: Game, level: Level, menu: Menu) -> None:
    """Test the pop_level method."""
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
    """Test the clear_levels method."""
    assert game.levels == []
    game.clear_levels()
    assert game.levels == []
    game.push_level(level)
    game.push_level(menu)
    assert game.levels == [level, menu]
    game.clear_levels()
    assert game.levels == []


def test_level(game: Game, level: Level, menu: Menu) -> None:
    """Test the level property."""
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


def test_before_run(game: Game, window: Window) -> None:
    """Test the before_run event."""

    @game.event
    def before_run() -> None:
        raise BeforeRunWorks

    with raises(BeforeRunWorks):
        game.run(window)
    window.close()


def test_run(
    game: Game, level: Level, window: Window, context: Context
) -> None:
    """Test the run method."""

    @level.event
    def on_push() -> None:
        assert game.level is level
        assert game.audio_context is context
        assert isinstance(game.music_sound_manager, SoundManager)
        assert game.music_sound_manager.context is game.audio_context
        assert game.music_sound_manager.default_looping is True
        assert isinstance(game.ambiance_sound_manager, SoundManager)
        assert game.ambiance_sound_manager.context is game.audio_context
        assert game.ambiance_sound_manager.default_looping is True
        assert isinstance(game.interface_sound_manager, SoundManager)
        assert game.interface_sound_manager.context is game.audio_context
        assert game.interface_sound_manager.default_looping is False
        schedule_once(lambda dt: window.close(), 0.2)

    game.run(window, initial_level=level)
    assert game.level is level


def test_get_settings_path() -> None:
    """Test the get_settings_path method."""
    g: Game = Game()
    assert g.get_settings_path() == Path(get_settings_path("earwax.game"))
    g = Game(name="testing")
    assert g.get_settings_path() == Path(get_settings_path("testing"))


def test_after_run(game: Game, level: Level, window: Window) -> None:
    """Test the after_run event."""

    @level.event
    def on_push() -> None:
        assert game.level is level
        schedule_once(lambda dt: window.close(), 0)

    @game.event
    def after_run() -> None:
        raise AfterRunWorks

    with raises(AfterRunWorks):
        game.run(window, initial_level=level)


def test_stop(game: Game, window: Window) -> None:
    """Test the stop method."""
    with raises(GameNotRunning):
        game.stop()

    @game.event
    def before_run() -> None:
        schedule_once(lambda dt: game.stop(), 0.5)

    game.run(window)


def test_push_action_menu(game: Game, level: Level) -> None:
    """Test the push_action_menu method."""

    @level.action("Test", symbol=key.T)
    def do_test() -> None:
        pass

    game.push_level(level)
    menu: ActionMenu = game.push_action_menu(input_mode=None)
    assert game.level is menu
    assert menu.game is game
    assert len(menu.items) == 1


def test_push_credits_menu(game: Game) -> None:
    """Test the push_credits_menu method."""
    game.credits = [
        Credit("Test 1", "example.com"),
        Credit("Test 2", "test.org"),
    ]
    m: Menu = game.push_credits_menu()
    assert isinstance(m, Menu)
    assert m is game.level
    assert len(m.items) == 2
    assert m.items[0].title == "Test 1"
    assert m.items[1].title == "Test 2"


def test_adjust_volume(game: Game) -> None:
    """Test adjusting the master volume."""
    game.config.sound.max_volume.value = 0.5
    assert game.adjust_volume(0.1) == 0.5
    assert game.config.sound.master_volume.value == 0.5
    assert game.adjust_volume(-0.1) == 0.4
    assert game.config.sound.master_volume.value == 0.4
    assert game.adjust_volume(-1.0) == 0.0
    assert game.config.sound.master_volume.value == 0.0


def test_set_volume(game: Game) -> None:
    """Test setting the volume exactly."""
    assert game.audio_context is not None
    game.set_volume(0.5)
    assert game.config.sound.master_volume.value == 0.5
    sleep(0.1)
    assert game.audio_context.gain == 0.5
    game.set_volume(2.0)
    assert game.config.sound.master_volume.value == 2.0
    sleep(0.1)
    assert game.audio_context.gain == 2.0
    game.set_volume(1.0)
    sleep(0.1)
    assert game.audio_context.gain == 1.0


def test_reveal_level(game: Game, level: Level) -> None:
    """Test the reveal_level method."""
    game.push_level(level)
    assert game.reveal_level(level) == 0
    assert game.level is level
    assert game.levels == [level]
    l1: Level = Level(game)
    l2: Level = Level(game)
    game.push_level(l1)
    game.push_level(l2)
    assert game.reveal_level(l1) == 1
    assert game.level is l1
    assert game.levels == [level, l1]
    game.push_level(l2)
    assert game.reveal_level(level) == 2
    assert game.level is level
    assert game.levels == [level]


def test_cancel(game: Game, level: Level) -> None:
    """Test the cancel method."""
    game.push_level(level)
    game.cancel()
    assert game.level is None
    level_2: Level = Level(game)
    game.push_level(level)
    game.push_level(level_2)
    game.cancel(level=level_2)
    assert game.level is level_2
    assert game.levels == [level, level_2]


def test_input_modes(game: Game) -> None:
    """Test input modes."""
    assert game.input_mode is InputModes.keyboard
    game.on_joybutton_press(PretendJoystick(), 0)
    assert game.input_mode is InputModes.controller
    game.on_key_press(1234, 0)
    assert game.input_mode is InputModes.keyboard
    game.on_joybutton_release(PretendJoystick(), 1)
    assert game.input_mode is InputModes.controller
    game.on_key_release(1234, 0)
    assert game.input_mode is InputModes.keyboard
    game.input_mode = InputModes.controller
    game.on_mouse_press(0, 0, 0, 0)
    assert game.input_mode is InputModes.keyboard
    game.input_mode = InputModes.controller
    game.on_mouse_release(0, 0, 0, 0)
    assert game.input_mode is InputModes.keyboard
