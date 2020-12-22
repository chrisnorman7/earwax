"""Test the general parts of the sound module."""

from pathlib import Path

from attr.exceptions import FrozenInstanceError
from pyglet.clock import schedule_once
from pyglet.window import Window
from pytest import raises
from synthizer import Buffer, SynthizerError

from earwax import BufferDirectory, Game, Level, SoundManager, get_buffer


def test_get_buffer():
    """Test the get_buffer method."""
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
    # Check that the buffers are cached:
    assert get_buffer('file', 'sound.wav') is b


def test_buffer_directory():
    """Test the BufferDirectory class."""
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
    """Test the gain of the various sound managers."""

    def do_test(dt: float) -> None:
        manager: SoundManager = game.interface_sound_manager
        expected: float = game.config.sound.sound_volume.value
        assert isinstance(manager, SoundManager)
        assert manager.source.gain == expected
        assert manager.gain == expected
        manager = game.music_sound_manager
        expected = game.config.sound.music_volume.value
        assert isinstance(manager, SoundManager)
        assert manager.source.gain == expected
        assert manager.gain == expected
        manager = game.ambiance_sound_manager
        expected = game.config.sound.ambiance_volume.value
        assert isinstance(manager, SoundManager)
        assert manager.source.gain == expected
        assert manager.gain == expected
        window.close()

    @game.event
    def before_run() -> None:
        schedule_once(do_test, 0.5)

    game.run(window, initial_level=level)
