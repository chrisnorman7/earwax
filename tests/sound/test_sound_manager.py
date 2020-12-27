"""Test the SoundManager class."""

from pathlib import Path
from time import sleep

from pyglet.clock import schedule_once
from pyglet.window import Window
from pytest import raises
from synthizer import (Buffer, BufferGenerator, Context, Source3D,
                       StreamingGenerator, SynthizerError)

from earwax import AlreadyDestroyed, Sound, SoundManager


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


def test_destroy_sound(
    context: Context, sound_manager: SoundManager, sound: Sound,
    source: Source3D
) -> None:
    """Make sure we can destroy sound successfully."""
    sound_manager.register_sound(sound)
    sound_manager.destroy_sound(sound)
    assert sound_manager.sounds == []
    assert sound._valid is False
    assert sound.context is context
    assert sound.source is source
    assert isinstance(sound.buffer, Buffer)
    assert isinstance(sound.generator, BufferGenerator)
    with raises(SynthizerError):
        sound.generator.destroy()
    with raises(AlreadyDestroyed) as exc:
        sound.destroy()
    assert exc.value.args == (sound,)


def test_destroy_all(
    sound_manager: SoundManager, context: Context, source: Source3D
) -> None:
    """Make sure we can destroy all sounds."""
    x: int
    for x in range(5):
        sound_manager.register_sound(
            Sound.from_path(context, source, Path('sound.wav'))
        )
    assert len(sound_manager.sounds) == 5
    sound_manager.destroy_all()
    assert sound_manager.sounds == []


def test_play_path(sound_manager: SoundManager, window: Window) -> None:
    """Test the play_path method."""
    sound_1: Sound = sound_manager.play_path(Path('sound.wav'), False)
    sound_2: Sound = sound_manager.play_path(Path('sound.wav'), True)

    def inner(dt: float) -> None:
        """Make sure the sound is still there."""
        assert sound_manager.sounds == [sound_1]
        assert sound_1._valid is True
        assert sound_2._valid is False
        window.close()

    assert sound_1.buffer is not None
    schedule_once(inner, sound_1.buffer.get_length_in_seconds() * 4)
    assert isinstance(sound_1, Sound)
    assert isinstance(sound_2, Sound)
    assert sound_1.context is sound_manager.context
    assert sound_2.context is sound_manager.context
    assert sound_1.source is sound_manager.source
    assert sound_2.source is sound_manager.source
    assert isinstance(sound_1.generator, BufferGenerator)
    assert isinstance(sound_2.generator, BufferGenerator)
    assert sound_1._valid
    assert sound_2._valid


def test_play_stream(sound_manager: SoundManager) -> None:
    """Test the play_stream method."""
    sound: Sound = sound_manager.play_stream('file', 'sound.wav')
    assert isinstance(sound, Sound)
    assert sound.context is sound_manager.context
    assert sound.source is sound_manager.source
    assert isinstance(sound.generator, StreamingGenerator)
    assert sound.buffer is None
    assert sound._valid is True


def test_play_path_looping(sound_manager: SoundManager) -> None:
    """Ensure that play path properly loops the sound."""
    sound_manager.should_loop = True
    s: Sound = sound_manager.play_path(Path('sound.wav'), False)
    sleep(0.2)
    assert s.generator.looping is True


def test_play_stream_looping(sound_manager: SoundManager) -> None:
    """Test that play_stream properly loops the sound."""
    sound_manager.should_loop = True
    s: Sound = sound_manager.play_stream('file', 'sound.wav')
    sleep(0.2)
    assert s.generator.looping is True


def test_del(context: Context, source: Source3D) -> None:
    """Ensure all sounds are destroyed when deleting a sound manager."""
    manager: SoundManager = SoundManager(context, source)
    manager.play_path(Path('sound.wav'), False)
    manager.play_stream('file', 'sound.wav')
    del manager
    with raises(SynthizerError):
        source.destroy()
