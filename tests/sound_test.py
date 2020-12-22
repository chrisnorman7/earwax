"""Test the sound system."""

from pathlib import Path
from time import sleep

from attr.exceptions import FrozenInstanceError
from pyglet.clock import schedule_once
from pyglet.window import Window
from pytest import raises
from synthizer import (Buffer, BufferGenerator, Context, Source, Source3D,
                       StreamingGenerator, SynthizerError)

from earwax import (AlreadyDestroyed, BufferDirectory, Game, Level, Sound,
                    SoundManager, get_buffer)


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


def test_sound_init(context: Context, source: Source3D) -> None:
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


def test_sound_from_path(context: Context, source: Source3D) -> None:
    """Test the Sound.from_path method."""
    sound: Sound = Sound.from_path(context, source, Path('sound.wav'))
    assert isinstance(sound, Sound)
    assert sound.context is context
    assert sound.source is source
    assert isinstance(sound.generator, BufferGenerator)
    assert isinstance(sound.buffer, Buffer)
    assert sound._valid is True
    assert sound.is_stream is False


def test_sound_destroy(context: Context, source: Source) -> None:
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


def test_sound_manager_init(sound_manager: SoundManager) -> None:
    """Test sound manager initialisation."""
    assert isinstance(sound_manager, SoundManager)
    assert isinstance(sound_manager.context, Context)
    assert isinstance(sound_manager.source, Source3D)
    assert sound_manager.should_loop is False
    assert sound_manager.sounds == []


def test_sound_manager_gain(sound_manager: SoundManager) -> None:
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


def test_sound_manager_register_sound(
    sound_manager: SoundManager, sound: Sound
) -> None:
    """Check we can register a sound properly."""
    assert sound_manager.sounds == []
    sound_manager.register_sound(sound)
    assert sound_manager.sounds == [sound]


def test_sound_manager_remove_sound(
    sound_manager: SoundManager, sound: Sound
) -> None:
    """Make sure we can remove a sound."""
    sound_manager.register_sound(sound)
    sound_manager.remove_sound(sound)
    assert sound_manager.sounds == []
