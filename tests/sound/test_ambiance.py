"""Test the Ambiance class."""

from pathlib import Path
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


def test_stop(context: Context) -> None:
    """Make sure we can stop the ambiance."""
    a: Ambiance = Ambiance('file', 'sound.wav', coordinates=Point(3, 4, 5))
    a.play(context, 1.0)
    a.stop()
    assert a.sound is None
    assert isinstance(a.sound_manager, SoundManager)
    assert a.sound_manager.sounds == []


def test_set_position(context: Context) -> None:
    """Make sure we can set the position of an ambiance."""
    a: Ambiance = Ambiance('file', 'sound.wav')
    a.play(context, 1.0)
    assert a.sound_manager is not None
    assert a.sound_manager.source.position == (0, 0, 0)
    a.set_position(Point(4, 4, 4))
    sleep(0.5)
    assert a.sound_manager.source.position == (4, 4, 4)
    a.set_position(Point(1, 2, 3))
    sleep(0.5)
    assert a.sound_manager.source.position == (1, 2, 3)


def test_from_path() -> None:
    """Test the from_path constructor."""
    a: Ambiance = Ambiance.from_path(Path('sound.wav'))
    assert isinstance(a, Ambiance)
    assert a.protocol == 'file'
    assert a.path == 'sound.wav'
    assert a.coordinates == Point(0, 0, 0)
    a = Ambiance.from_path(Path('sound.wav'), coordinates=Point(4, 5, 6))
    assert a.protocol == 'file'
    assert a.path == 'sound.wav'
    assert a.coordinates == Point(4, 5, 6)
