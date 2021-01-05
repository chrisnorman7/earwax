"""Test the general parts of the sound module."""

from pathlib import Path
from typing import Optional

from attr.exceptions import FrozenInstanceError
from pyglet.clock import schedule_once
from pyglet.window import Window
from pytest import raises
from synthizer import Buffer, SynthizerError

from earwax import BufferCache, BufferDirectory, Game, Level, SoundManager


def test_buffer_cache(buffer_cache: BufferCache, game: Game) -> None:
    """Test the fixture, and initialisation."""
    assert isinstance(buffer_cache, BufferCache)
    assert buffer_cache is game.buffer_cache
    assert buffer_cache.max_size == game.config.sound.default_cache_size.value
    assert buffer_cache.current_size == 0
    assert buffer_cache.buffer_uris == []
    assert buffer_cache.buffers == {}


def test_get_buffer(buffer_cache: BufferCache):
    """Test the get_buffer method."""
    b = buffer_cache.get_buffer('file', 'sound.wav')
    assert isinstance(b, Buffer)
    assert len(buffer_cache.buffer_uris) == 1
    uri: str = buffer_cache.buffer_uris[0]
    assert buffer_cache.buffers[uri] is b
    assert buffer_cache.current_size == buffer_cache.get_size(b)
    # Try to get a non existant file.
    with raises(SynthizerError):
        buffer_cache.get_buffer('file', 'invalid.wav')
    # Try to open an invalid file.
    with raises(SynthizerError):
        buffer_cache.get_buffer('file', __file__)
    # Try to open a directory.
    with raises(SynthizerError):
        buffer_cache.get_buffer('file', 'earwax')
    # Check that the buffers are cached:
    assert buffer_cache.get_buffer('file', 'sound.wav') is b
    # Check the size is still as it was.
    assert buffer_cache.current_size == buffer_cache.get_size(b)


def test_current_size(buffer_cache: BufferCache) -> None:
    """Test the current_size attribute."""
    b1: Buffer = buffer_cache.get_buffer('file', 'sound.wav')
    b2: Buffer = buffer_cache.get_buffer('file', 'move.wav')
    assert buffer_cache.current_size == (
        buffer_cache.get_size(b1) + buffer_cache.get_size(b2)
    )


def test_pop_buffer(buffer_cache: BufferCache) -> None:
    """Test that maximum size is respected."""
    buffer_cache.get_buffer('file', 'sound.wav')
    uri: str = buffer_cache.buffer_uris[0]
    buffer_cache.get_buffer('file', 'move.wav')
    assert uri == buffer_cache.buffer_uris[-1]
    buffer_cache.pop_buffer()
    assert uri not in buffer_cache.buffer_uris
    assert len(buffer_cache.buffer_uris) == 1
    assert len(buffer_cache.buffers) == 1


def test_max_size(buffer_cache: BufferCache) -> None:
    """Test that maximum size is respected."""
    b1: Buffer = buffer_cache.get_buffer('file', 'sound.wav')
    uri: str = buffer_cache.buffer_uris[0]
    s1: int = buffer_cache.get_size(b1)
    buffer_cache.max_size = s1
    b2: Buffer = buffer_cache.get_buffer('file', 'move.wav')
    assert uri not in buffer_cache.buffer_uris
    s2: int = buffer_cache.get_size(b2)
    assert len(buffer_cache.buffer_uris) == 1
    assert buffer_cache.current_size == s2
    with raises(SynthizerError):
        b1.destroy()
    assert buffer_cache.buffers[buffer_cache.buffer_uris[0]] is b2


def test_buffer_directory(buffer_cache: BufferCache):
    """Test the BufferDirectory class."""
    with raises(SynthizerError):
        # This test will throw an error because of non sound files.
        BufferDirectory(buffer_cache, Path())
    b: BufferDirectory = BufferDirectory(
        buffer_cache, Path.cwd(), glob='*.wav'
    )
    assert isinstance(b.buffer_cache, BufferCache)
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
        b.path = Path.cwd()  # type: ignore[misc]


def test_gains(game: Game, window: Window, level: Level) -> None:
    """Test the gain of the various sound managers."""

    def do_test(dt: float) -> None:
        manager: Optional[SoundManager] = game.interface_sound_manager
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
