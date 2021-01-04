"""Test classes from the trigger_map module."""

from earwax.cmd.trigger_map import Trigger


def test_init() -> None:
    """Test initialisation."""
    t: Trigger = Trigger()
    assert t.symbol is None
    assert t.modifiers == []
    assert t.joystick_button is None
    assert t.mouse_button is None
    assert t.hat_directions is None
