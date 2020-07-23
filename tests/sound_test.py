"""Test the sound system."""

from pytest import raises, mark

from earwax import get_buffer
from synthizer import Buffer, SynthizerError


@mark.skip(reason='Synthizer is too unstable.')
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
