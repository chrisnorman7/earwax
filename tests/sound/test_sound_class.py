"""Test the Sound class."""

from pathlib import Path
from time import sleep

from pyglet.window import Window
from pytest import raises
from synthizer import (Buffer, BufferGenerator, Context, GlobalFdnReverb,
                       Source, Source3D, StreamingGenerator, SynthizerError)

from earwax import AlreadyDestroyed, BufferCache, Game, Sound


def test_init(
    buffer_cache: BufferCache, context: Context, source: Source3D
) -> None:
    """Test initialisation."""
    buffer: Buffer = buffer_cache.get_buffer('file', 'sound.wav')
    generator: BufferGenerator = BufferGenerator(context)
    sound: Sound = Sound(context, source, generator, buffer)
    assert sound.context is context
    assert sound.source is source
    assert sound.generator is generator
    assert sound.buffer is buffer
    assert sound._valid is True


def test_from_stream(context: Context, source: Source3D) -> None:
    """Test the Sound.from_stream method."""
    sound: Sound = Sound.from_stream(context, source, 'file', 'sound.wav')
    assert isinstance(sound, Sound)
    assert sound.context is context
    assert sound.source is source
    assert isinstance(sound.generator, StreamingGenerator)
    assert sound._valid is True
    assert sound.is_stream is True


def test_from_path(
    buffer_cache: BufferCache, context: Context, source: Source3D
) -> None:
    """Test the Sound.from_path method."""
    sound: Sound = Sound.from_path(
        context, source, buffer_cache, Path('sound.wav')
    )
    assert isinstance(sound, Sound)
    assert sound.context is context
    assert sound.source is source
    assert isinstance(sound.generator, BufferGenerator)
    assert isinstance(sound.buffer, Buffer)
    assert sound._valid is True
    assert sound.is_stream is False


def test_destroy_sound_from_path(
    buffer_cache: BufferCache, context: Context, source: Source
) -> None:
    """Make sure we can destroy sounds."""
    sound: Sound = Sound.from_path(
        context, source, buffer_cache, Path('sound.wav')
    )
    sound.destroy()
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


def test_destroy_from_stream(context: Context, source: Source) -> None:
    """Make sure we can destroy a streamed sound."""
    sound: Sound = Sound.from_stream(context, source, 'file', 'sound.wav')
    sound.destroy()
    assert sound._valid is False
    assert sound.context is context
    assert sound.source is source
    assert sound.buffer is None
    assert isinstance(sound.generator, StreamingGenerator)
    with raises(SynthizerError):
        sound.generator.destroy()
    with raises(AlreadyDestroyed) as exc:
        sound.destroy()
    assert exc.value.args == (sound,)


def test_schedule_destruction(
    buffer_cache: BufferCache, game: Game, window: Window, context: Context,
    source: Source3D
) -> None:
    """Ensure sounds get destroyed properly."""
    sound: Sound = Sound.from_stream(context, source, 'file', 'sound.wav')
    with raises(RuntimeError):
        sound.schedule_destruction()
    assert sound._valid is True
    sound.destroy()
    sound = Sound.from_path(context, source, buffer_cache, Path('sound.wav'))
    sound.schedule_destruction(lambda: window.close())
    game.run(window)
    assert sound._valid is False
    assert sound.context is context
    assert sound.source is source
    assert isinstance(sound.buffer, Buffer)
    assert isinstance(sound.generator, BufferGenerator)
    with raises(SynthizerError):
        sound.generator.destroy()


def test_connect_reverb(reverb: GlobalFdnReverb, sound: Sound) -> None:
    """Make sure we can easily attach reverb."""
    # First make sure we've not messed up the fixture.
    assert isinstance(reverb, GlobalFdnReverb)
    sound.connect_reverb(reverb)


def test_restart(sound: Sound) -> None:
    """Make sure we can restart a sound."""
    sleep(0.3)
    assert sound.generator.position > 0.2
    sound.source.remove_generator(sound.generator)
    sound.restart()
    sleep(0.5)
    assert sound.generator.position == 0.0


def test_pause(sound: Sound) -> None:
    """Test the pause method."""
    sound.pause()
    assert sound.paused is True
    assert sound._paused is True


def test_play(sound: Sound) -> None:
    """Test the play method."""
    sound.pause()
    assert sound.paused is True
    sound.play()
    assert sound.paused is False
    assert sound._paused is False


def test_paused(sound: Sound) -> None:
    """Test the paused property."""
    sound.paused = True
    assert sound.paused is True
    assert sound._paused is True
    sound.paused = False
    assert sound.paused is False
    assert sound._paused is False
