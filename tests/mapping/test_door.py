"""Test the earwax.Door class."""

from pathlib import Path

from earwax import Door


def test_init(door: Door) -> None:
    """Test initialisation."""
    assert isinstance(door, Door)
    assert door.open is True
    assert door.closed_sound == Path("sound.wav")
    assert door.close_sound == Path("sound.wav")
    assert door.open_sound == Path("sound.wav")
    door = Door()
    assert door.closed_sound is None
    assert door.open_sound is None
    assert door.close_sound is None
