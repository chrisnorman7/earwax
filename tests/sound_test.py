"""Test the sound system."""

from pathlib import Path
from pytest import raises
from synthizer import Buffer, SynthizerError

from earwax import get_buffer, BufferDirectory


def test_get_buffer():
    b = get_buffer('file', 'sound.wav')
    assert isinstance(b, Buffer)
    # Try to get a non existant file.
    with raises(SynthizerError):
        get_buffer('file', 'invalid.wav')
    # Try to open an invalid file.
    with raises(SynthizerError):
        get_buffer('file', __file__)
    # Try to open a directory.
    with raises(SynthizerError):
        get_buffer('file', 'earwax')


def test_buffer_directory():
    with raises(SynthizerError):
        BufferDirectory(Path())  # Errors because of non sound files.
    b: BufferDirectory = BufferDirectory(Path.cwd(), glob='*.wav')
    assert len(b.buffers) == 2
    assert isinstance(b.buffers['move.wav'], Buffer)
    assert isinstance(b.buffers['sound.wav'], Buffer)
    with raises(KeyError):
        b.buffers['nothing.wav']
    assert b.buffers['move.wav'] != b.buffers['sound.wav']
