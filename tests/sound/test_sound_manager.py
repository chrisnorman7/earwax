"""Test the SoundManager class."""

from pathlib import Path
from time import sleep

from pyglet.clock import schedule_once
from pyglet.window import Window
from pytest import raises
from synthizer import (Buffer, BufferGenerator, Context, DirectSource,
                       StreamingGenerator)

from earwax import AlreadyDestroyed, BufferCache, NoCache, Sound, SoundManager


def test_init(sound_manager: SoundManager) -> None:
    """Test sound manager initialisation."""
    assert isinstance(sound_manager, SoundManager)
    assert isinstance(sound_manager.context, Context)
    assert sound_manager.default_looping is False
    assert isinstance(sound_manager.buffer_cache, BufferCache)
    assert sound_manager.sounds == []
    assert sound_manager.default_gain == 1.0
    assert sound_manager.default_position is None
    assert sound_manager.default_reverb is None


def test_register_sound(
    sound_manager: SoundManager, sound: Sound
) -> None:
    """Check we can register a sound properly."""
    assert sound.on_destroy is None
    assert sound_manager.sounds == []
    sound_manager.register_sound(sound)
    assert sound_manager.sounds == [sound]
    assert sound.on_destroy == sound_manager.remove_sound


def test_remove_sound(
    sound_manager: SoundManager, sound: Sound
) -> None:
    """Make sure we can remove a sound."""
    assert sound.on_destroy is None
    sound_manager.register_sound(sound)
    assert sound.on_destroy == sound_manager.remove_sound
    sound_manager.remove_sound(sound)
    assert sound_manager.sounds == []
    assert sound.on_destroy is None


def test_destroy_sound(
    context: Context, sound_manager: SoundManager, sound: Sound
) -> None:
    """Make sure we can destroy sound successfully."""
    sound_manager.register_sound(sound)
    assert sound in sound_manager.sounds
    sound.destroy()
    assert sound_manager.sounds == []
    assert sound._destroyed is True
    assert sound.context is context
    assert sound.source is None
    assert isinstance(sound.buffer, Buffer)
    assert isinstance(sound.generator, BufferGenerator)
    assert sound.on_destroy is None
    with raises(AlreadyDestroyed) as exc:
        sound.destroy()
    assert exc.value.args == (sound,)


def test_destroy_all(sound_manager: SoundManager, context: Context) -> None:
    """Make sure we can destroy all sounds."""
    assert sound_manager.buffer_cache is not None
    x: int
    for x in range(5):
        sound_manager.play_path(Path('sound.wav'))
    assert len(sound_manager.sounds) == 5
    sound_manager.destroy_all()
    assert sound_manager.sounds == []


def test_play_path(sound_manager: SoundManager, window: Window) -> None:
    """Test the play_path method."""
    sound_1: Sound = sound_manager.play_path(
        Path('sound.wav'), keep_around=False
    )
    sound_2: Sound = sound_manager.play_path(Path('sound.wav'))
    assert sound_manager.sounds == [sound_1, sound_2]

    def inner(dt: float) -> None:
        """Make sure the sound is still there."""
        assert sound_manager.sounds == [sound_1]
        assert sound_1._destroyed is False
        assert sound_2._destroyed is True
        window.close()

    assert sound_1.buffer is not None
    schedule_once(inner, sound_1.buffer.get_length_in_seconds() * 4)
    assert isinstance(sound_1, Sound)
    assert isinstance(sound_2, Sound)
    assert sound_1.context is sound_manager.context
    assert sound_2.context is sound_manager.context
    assert isinstance(sound_1.source, DirectSource)
    assert isinstance(sound_2.source, DirectSource)
    assert isinstance(sound_1.generator, BufferGenerator)
    assert isinstance(sound_2.generator, BufferGenerator)
    assert sound_1._destroyed is False
    assert sound_2._destroyed is False


def test_play_stream(sound_manager: SoundManager) -> None:
    """Test the play_stream method."""
    sound: Sound = sound_manager.play_stream('file', 'sound.wav')
    assert isinstance(sound, Sound)
    assert sound.context is sound_manager.context
    assert isinstance(sound.source, DirectSource)
    assert sound_manager.sounds == [sound]
    assert isinstance(sound.generator, StreamingGenerator)
    assert sound.buffer is None
    assert sound._destroyed is False


def test_play_path_looping(sound_manager: SoundManager) -> None:
    """Ensure that play path properly loops the sound."""
    sound_manager.default_looping = True
    s: Sound = sound_manager.play_path(Path('sound.wav'))
    sleep(0.2)
    assert s.generator.looping is True


def test_play_stream_looping(sound_manager: SoundManager) -> None:
    """Test that play_stream properly loops the sound."""
    sound_manager.default_looping = True
    s: Sound = sound_manager.play_stream('file', 'sound.wav')
    sleep(0.2)
    assert s.generator.looping is True


def test_no_cache(
    buffer_cache: BufferCache, sound_manager: SoundManager
) -> None:
    """Test trying to play a path with no buffer cache."""
    sound_manager.buffer_cache = None
    with raises(NoCache):
        sound_manager.play_path(Path('sound.wav'))
    sound_manager.buffer_cache = buffer_cache
    s: Sound = sound_manager.play_path(Path('sound.wav'), keep_around=False)
    assert isinstance(s, Sound)
    s.destroy()
