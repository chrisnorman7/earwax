"""Test the SoundManager class."""

from time import sleep

from synthizer import Context, Source3D

from earwax import Sound, SoundManager


def test_init(sound_manager: SoundManager) -> None:
    """Test sound manager initialisation."""
    assert isinstance(sound_manager, SoundManager)
    assert isinstance(sound_manager.context, Context)
    assert isinstance(sound_manager.source, Source3D)
    assert sound_manager.should_loop is False
    assert sound_manager.sounds == []


def test_gain(sound_manager: SoundManager) -> None:
    """Test SoundManager.gain."""
    assert sound_manager.gain == 1.0
    assert sound_manager._gain == 1.0
    assert sound_manager.source.gain == 1.0
    sound_manager.gain = 0.5
    assert sound_manager._gain == 0.5
    assert sound_manager.gain == 0.5
    # We need to wait a little while, because Synthizer doesn't read properties
    # in realtime.
    sleep(0.5)
    assert sound_manager.source.gain == 0.5


def test_register_sound(
    sound_manager: SoundManager, sound: Sound
) -> None:
    """Check we can register a sound properly."""
    assert sound_manager.sounds == []
    sound_manager.register_sound(sound)
    assert sound_manager.sounds == [sound]


def test_remove_sound(
    sound_manager: SoundManager, sound: Sound
) -> None:
    """Make sure we can remove a sound."""
    sound_manager.register_sound(sound)
    sound_manager.remove_sound(sound)
    assert sound_manager.sounds == []
