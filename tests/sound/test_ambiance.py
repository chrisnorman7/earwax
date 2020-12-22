"""Test the Ambiance class."""

from time import sleep

from synthizer import Context, Source3D

from earwax import Ambiance, Point, Sound, SoundManager


def test_init() -> None:
    """Test initialisation."""
    a: Ambiance = Ambiance('file', 'sound.wav')
    assert a.protocol == 'file'
    assert a.path == 'sound.wav'
    assert a.coordinates == Point(0, 0, 0)
    assert a.sound_manager is None
    assert a.sound is None


def test_play(context: Context) -> None:
    """Test the play method."""
    a: Ambiance = Ambiance('file', 'sound.wav', coordinates=Point(3, 4, 5))
    a.play(context, 0.5)
    assert isinstance(a.sound_manager, SoundManager)
    assert isinstance(a.sound, Sound)
    assert a.sound_manager.context is context
    assert isinstance(a.sound_manager.source, Source3D)
    assert a.coordinates == Point(3, 4, 5)
    sleep(0.5)
    assert a.sound_manager.source.position == a.coordinates.coordinates
    assert a.sound_manager.gain == 0.5
