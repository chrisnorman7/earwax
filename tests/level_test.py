"""Test level instances."""

from earwax import Action, Game, Level


def test_init(level: Level, game: Game) -> None:
    assert isinstance(level, Level)
    assert level.game is game
    assert level.actions == []
    assert level.motions == {}
    assert level.triggered_actions == []
    assert level.on_key_release_generators == {}


def test_action(game: Game, level: Level) -> None:
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
