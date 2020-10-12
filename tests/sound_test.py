"""Test the sound system."""

from pathlib import Path
from typing import Optional

from attr.exceptions import FrozenInstanceError
from pyglet.clock import schedule_once
from pyglet.window import Window
from pytest import raises
from synthizer import Buffer, SynthizerError

from earwax import (
    AdvancedInterfaceSoundPlayer, BufferDirectory, Game, Level, get_buffer)


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
    assert isinstance(b.paths['sound.wav'], Path)
    assert isinstance(b.paths['move.wav'], Path)
    assert b.paths['sound.wav'] != b.paths['move.wav']
    with raises(KeyError):
        b.paths['nothing.wav']
    assert isinstance(b.random_path(), Path)
    p: Path = b.random_path()
    assert b.paths[p.name] is p
    with raises(FrozenInstanceError):
        b.path = Path.cwd()


def test_gain(game: Game, window: Window, level: Level) -> None:

    def do_test(dt: float) -> None:
        i: Optional[AdvancedInterfaceSoundPlayer] = game.interface_sound_player
        expected: float = game.config.sound.sound_volume.value
        assert i is not None
        assert i.source.gain == expected
        assert i.gain == expected
        window.close()

    @game.event
    def before_run() -> None:
        schedule_once(do_test, 0)

    game.run(window, initial_level=level)
