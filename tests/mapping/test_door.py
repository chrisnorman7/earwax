"""Test the earwax.Door class."""

from earwax import Door


def test_init() -> None:
    """Test initialisation."""
    d = Door()
    assert d.open is True
    assert d.closed_sound is None
    assert d.open_sound is None
    assert d.close_sound is None
