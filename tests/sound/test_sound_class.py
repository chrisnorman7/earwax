"""Test the Sound class."""

from pathlib import Path

from pytest import raises
from synthizer import (Buffer, BufferGenerator, Context, Source, Source3D,
                       StreamingGenerator, SynthizerError)

from earwax import AlreadyDestroyed, Sound, get_buffer


def test_init(context: Context, source: Source3D) -> None:
    """Test initialisation."""
    buffer: Buffer = get_buffer('file', 'sound.wav')
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


def test_from_path(context: Context, source: Source3D) -> None:
    """Test the Sound.from_path method."""
    sound: Sound = Sound.from_path(context, source, Path('sound.wav'))
    assert isinstance(sound, Sound)
    assert sound.context is context
    assert sound.source is source
    assert isinstance(sound.generator, BufferGenerator)
    assert isinstance(sound.buffer, Buffer)
    assert sound._valid is True
    assert sound.is_stream is False


def test_destroy(context: Context, source: Source) -> None:
    """Make sure we can destroy sounds."""
    sound: Sound = Sound.from_path(context, source, Path('sound.wav'))
    sound.destroy()
    assert sound.context is context
    assert sound.source is source
    assert isinstance(sound.buffer, Buffer)
    assert isinstance(sound.generator, BufferGenerator)
    with raises(SynthizerError):
        sound.generator.destroy()
    sound.source.destroy()
    assert sound._valid is False
    with raises(AlreadyDestroyed) as exc:
        sound.destroy()
    assert exc.value.args == (sound,)
