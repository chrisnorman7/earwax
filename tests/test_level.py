"""Test level instances."""

from typing import List

from pyglet.clock import schedule_once
from pyglet.window import Window, key
from pytest import raises

from earwax import Action, Game, Level


class OnCoverWorks(Exception):
    """The on_cover event worked."""


class OnRevealWorks(Exception):
    """the on_reveal event worked."""


def test_init(level: Level, game: Game) -> None:
    """Test initialisation."""
    assert isinstance(level, Level)
    assert level.actions == []
    assert level.motions == {}


def test_on_text_motion(game: Game, level: Level, window: Window) -> None:
    """Test that text motions are handled properly."""
    motions: List[int] = []

    @level.event
    def on_text_motion(motion: int) -> None:
        """Add levels."""
        motions.append(motion)
        if motion == key.MOTION_BEGINNING_OF_LINE:
            window.close()

    def push_motions(dt: float) -> None:
        window.dispatch_event('on_text_motion', key.MOTION_BACKSPACE)
        window.dispatch_event('on_text_motion', key.MOTION_BEGINNING_OF_LINE)

    @game.event
    def before_run() -> None:
        schedule_once(push_motions, 0.1)

    game.run(window, initial_level=level)
    assert motions == [key.MOTION_BACKSPACE, key.MOTION_BEGINNING_OF_LINE]


def test_on_push(game: Game, level: Level) -> None:
    """Test the on_push event."""
    push_level: Level = Level(game)

    @level.event
    def on_push() -> None:
        game.push_level(push_level)

    game.push_level(level)
    assert game.levels == [level, push_level]


def test_on_pop(level: Level, game: Game) -> None:
    """Test the on_pop event."""
    pop_level: Level = Level(game)

    @level.event
    def on_pop() -> None:
        game.push_level(pop_level)
    game.push_level(level)
    game.pop_level()
    assert game.levels == [pop_level]


def test_on_reveal(game: Game, level: Level) -> None:
    """Test the on_reveal event."""
    covering_level: Level = Level(game)

    @level.event
    def on_reveal() -> None:
        raise OnRevealWorks()

    game.push_level(level)
    game.push_level(covering_level)
    with raises(OnRevealWorks):
        game.pop_level()


def test_action(game: Game, level: Level) -> None:
    """Test the game.action method."""
    game.push_level(level)
    a = level.action('Print')(print)
    assert isinstance(a, Action)
    assert a.title == 'Print'
    assert a.func is print
    assert a.symbol is None
    assert a.modifiers == 0
    assert a.interval is None
    assert a.last_run == 0.0
    assert level.actions == [a]


def test_on_cover(game: Game, level: Level) -> None:
    """Test the on_cover event."""
    l: Level = Level(game)

    @level.event
    def on_cover(lev: Level) -> None:
        assert lev is l
        raise OnCoverWorks()

    game.push_level(level)
    with raises(OnCoverWorks):
        game.push_level(l)
    assert game.level is level
    game.pop_level()
    assert game.level is None
    game.push_level(l)
    assert game.level is l
    game.push_level(level)
    assert game.level is level
