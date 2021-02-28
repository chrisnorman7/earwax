"""Test classes from the trigger_map module."""

from typing import Any, Dict

from earwax.cmd.game_level import (
    BoxLevelData,
    GameLevel,
    GameLevelScript,
    LevelData,
    Trigger,
)


def test_init() -> None:
    """Test initialisation."""
    t: Trigger = Trigger()
    assert t.symbol is None
    assert t.modifiers == []
    assert t.joystick_button is None
    assert t.mouse_button is None
    assert t.hat_directions is None


def test_game_level_script() -> None:
    """Test the GameLevelScript class."""
    t: Trigger = Trigger()
    code: str = 'def _():\n    print("works.")\n'
    s: GameLevelScript = GameLevelScript("Test Script", t)
    assert s.name == "Test Script"
    assert s.trigger is t
    assert s.code == ""
    try:
        s.code = code
        assert s.script_path.is_file()
        assert s.code == code
    finally:
        if s.script_path.is_file():
            s.script_path.unlink()


def test_box_level_data() -> None:
    """Test the BoxLevelData class."""
    d: BoxLevelData = BoxLevelData()
    assert d.bearing == 0


def test_game_level() -> None:
    """Test the GameLevel class."""
    t1: Trigger = Trigger(symbol="_1")
    t2: Trigger = Trigger(symbol="_2")
    s1: GameLevelScript = GameLevelScript("Test Script 1", t1, "First code")
    s2: GameLevelScript = GameLevelScript("Test Script 2", t2, "Second code")
    d: BoxLevelData = BoxLevelData(bearing=90)
    gl: GameLevel = GameLevel("Test BoxLevel", d, scripts=[s1, s2])
    assert gl.scripts == [s1, s2]
    assert gl.name == "Test BoxLevel"
    assert gl.data is d
    gl2: GameLevel = GameLevel.load(gl.dump())
    assert gl2 == gl


def test_level_data() -> None:
    """Test the LevelData class."""
    level_data: LevelData = LevelData()
    d: Dict[str, Any] = level_data.dump()[LevelData.__value_key__]
    assert isinstance(d, dict)
    assert d == {}
