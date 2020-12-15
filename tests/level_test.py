"""Test level instances."""

from pytest import raises

from earwax import Action, Game, Level


class OnCoverWorks(Exception):
    """The on_cover event worked."""


def test_init(level: Level, game: Game) -> None:
    """Test initialisation."""
    assert isinstance(level, Level)
    assert level.actions == []
    assert level.motions == {}


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
