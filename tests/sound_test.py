"""Test the sound system."""

from pytest import raises
from synthizer import Buffer, SynthizerError

from earwax import get_buffer


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
