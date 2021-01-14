"""Test the Ambiance class."""

from pathlib import Path

from synthizer import Source3D

from earwax import Ambiance, Point, Sound, SoundManager


def test_init() -> None:
    """Test initialisation."""
    a: Ambiance = Ambiance.from_path(
        Path('sound.wav'), coordinates=Point(0, 0, 0)
    )
    assert a.protocol == 'file'
    assert a.path == 'sound.wav'
    assert a.coordinates == Point(0, 0, 0)
    assert a.sound is None


def test_play(sound_manager: SoundManager) -> None:
    """Test the play method."""
    a: Ambiance = Ambiance('file', 'sound.wav', Point(3, 4, 5))
    assert a.coordinates == Point(3, 4, 5)
    a.play(sound_manager)
    assert isinstance(a.sound, Sound)
    assert a.sound.position == a.coordinates
    assert isinstance(a.sound.source, Source3D)
    a.play(sound_manager, gain=0.5)
    assert a.sound.gain == 0.5


def test_stop(sound_manager: SoundManager) -> None:
    """Make sure we can stop the ambiance."""
    a: Ambiance = Ambiance.from_path(Path('sound.wav'), Point(3, 4, 5))
    a.play(sound_manager)
    a.stop()
    assert a.sound is None
