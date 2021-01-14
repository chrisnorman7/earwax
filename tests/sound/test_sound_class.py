"""Test the Sound class."""

from pathlib import Path
from time import sleep

from pyglet.window import Window
from pytest import raises
from synthizer import (Buffer, BufferGenerator, Context, DirectSource,
                       Generator, GlobalFdnReverb, PannedSource,
                       PannerStrategy, Source3D, StreamingGenerator,
                       SynthizerError)

from earwax import AlreadyDestroyed, BufferCache, Game, Point, Sound
from earwax.sound import PannerStrategies


def test_init(
    buffer_cache: BufferCache, context: Context
) -> None:
    """Test initialisation."""
    generator: Generator = BufferGenerator(context)
    buffer: Buffer = buffer_cache.get_buffer('file', 'sound.wav')
    sound: Sound = Sound(context, generator, buffer)
    sleep(0.1)
    assert sound.context is context
    assert sound.generator is generator
    assert sound.buffer is buffer
    assert sound.panner_strategy is PannerStrategies.default
    assert sound.position is None
    assert isinstance(sound.source, DirectSource)
    assert not sound._destroyed
    assert sound.gain == 1.0
    assert sound.source.gain == 1.0
    assert sound.looping is False
    assert sound.generator.looping is False
    assert sound.is_stream is False
    sound.destroy()
    generator = StreamingGenerator(context, 'file', 'sound.wav')
    sound = Sound(
        context, generator, None, looping=True, gain=0.5,
        position=Point(1, 2, 3), panner_strategy=PannerStrategies.stereo
    )
    sleep(0.1)
    assert sound.buffer is None
    assert sound.panner_strategy is PannerStrategies.stereo
    assert sound.generator is generator
    assert sound.looping is True
    assert generator.looping is True
    assert isinstance(sound.source, Source3D)
    assert sound.position == Point(1, 2, 3)
    assert sound.source.position == (1, 2, 3)
    assert sound.is_stream is True
    assert sound.source.gain == 0.5
    assert sound.source.panner_strategy is PannerStrategy.STEREO
    sound.destroy()
    generator = StreamingGenerator(context, 'file', 'sound.wav')
    sound = Sound(
        context, generator, buffer, position=0.5,
        panner_strategy=PannerStrategies.best
    )
    sleep(0.1)
    assert isinstance(sound.source, PannedSource)
    assert sound.source.panning_scalar == 0.5
    assert sound.panner_strategy is PannerStrategies.best
    assert sound.source.panner_strategy is PannerStrategy.HRTF
    sound.destroy()


def test_from_stream(context: Context) -> None:
    """Test the Sound.from_stream method."""
    sound: Sound = Sound.from_stream(
        context, 'file', 'sound.wav', position=-1.0
    )
    assert isinstance(sound, Sound)
    sleep(0.1)
    assert sound.context is context
    assert isinstance(sound.source, PannedSource)
    assert isinstance(sound.generator, StreamingGenerator)
    assert sound._destroyed is False
    assert sound.is_stream is True
    assert sound.source.panning_scalar == -1.0


def test_from_path(buffer_cache: BufferCache, context: Context) -> None:
    """Test the Sound.from_path method."""
    sound: Sound = Sound.from_path(
        context, buffer_cache, Path('sound.wav')
    )
    assert isinstance(sound, Sound)
    assert sound.context is context
    assert isinstance(sound.generator, BufferGenerator)
    assert isinstance(sound.source, DirectSource)
    assert isinstance(sound.buffer, Buffer)
    assert sound._destroyed is False
    assert sound.is_stream is False


def test_destroy_sound_from_path(
    buffer_cache: BufferCache, context: Context
) -> None:
    """Make sure we can destroy sounds."""
    sound: Sound = Sound.from_path(
        context, buffer_cache, Path('sound.wav')
    )
    sound.destroy()
    assert sound._destroyed is True
    assert sound.context is context
    assert sound.source is None
    assert isinstance(sound.buffer, Buffer)
    assert isinstance(sound.generator, BufferGenerator)
    with raises(KeyError):
        sound.generator.destroy()
    with raises(AlreadyDestroyed) as exc:
        sound.destroy()
    assert exc.value.args == (sound,)


def test_destroy_from_stream(context: Context) -> None:
    """Make sure we can destroy a streamed sound."""
    sound: Sound = Sound.from_stream(context, 'file', 'sound.wav')
    sound.destroy()
    assert sound._destroyed is True
    assert sound.context is context
    assert sound.source is None
    assert sound.buffer is None
    assert isinstance(sound.generator, StreamingGenerator)
    with raises(KeyError):
        sound.generator.destroy()
    with raises(AlreadyDestroyed) as exc:
        sound.destroy()
    assert exc.value.args == (sound,)


def test_schedule_destruction(
    buffer_cache: BufferCache, game: Game, window: Window, context: Context
) -> None:
    """Ensure sounds get destroyed properly."""
    sound: Sound = Sound.from_stream(context, 'file', 'sound.wav')
    with raises(RuntimeError):
        sound.schedule_destruction()
    assert sound._destroyed is False
    sound.destroy()
    sound = Sound.from_path(
        context, buffer_cache, Path('sound.wav'),
        on_destroy=lambda sound: window.close()
    )
    sound.schedule_destruction()
    game.run(window)
    assert sound._destroyed is True
    assert sound.context is context
    assert sound.source is None
    assert isinstance(sound.buffer, Buffer)
    assert isinstance(sound.generator, BufferGenerator)
    with raises(KeyError):
        sound.generator.destroy()


def test_connect_reverb() -> None:
    """Make sure we can easily attach reverb."""
    context: Context = Context()
    reverb: GlobalFdnReverb = GlobalFdnReverb(context)
    buffer_cache: BufferCache = BufferCache(1024 ** 3)
    sound: Sound = Sound.from_path(context, buffer_cache, Path('sound.wav'))
    # First make sure we've not messed up the fixtures.
    assert isinstance(sound, Sound)
    assert isinstance(reverb, GlobalFdnReverb)
    sound.connect_reverb(reverb)
    assert sound.reverb is reverb
    sound.destroy()


def test_disconnect_reverb(reverb: GlobalFdnReverb, sound: Sound) -> None:
    """Make sure we can easily detach a reverb."""
    sound.connect_reverb(reverb)
    # sleep(1)
    sound.disconnect_reverb()
    # Unfortunately there is no way in Synthizer I know of to validate this
    # has worked.
    assert sound.reverb is None


def test_restart(sound: Sound) -> None:
    """Make sure we can restart a sound."""
    assert sound.source is not None
    sleep(0.3)
    assert sound.generator.position > 0.2
    sound.source.remove_generator(sound.generator)
    sound.restart()
    sleep(0.5)
    assert sound.generator.position == 0.0


def test_pause(sound: Sound) -> None:
    """Test the pause method."""
    sound.pause()
    sleep(0.1)
    position: float = sound.generator.position
    assert sound.paused is True
    assert sound._paused is True
    sleep(0.5)
    assert sound.generator.position == position


def test_play(sound: Sound) -> None:
    """Test the play method."""
    sound.pause()
    assert sound.paused is True
    sleep(0.1)
    position: float = sound.generator.position
    sound.play()
    assert sound.paused is False
    assert sound._paused is False
    sleep(0.5)
    assert sound.generator.position > position


def test_paused(sound: Sound) -> None:
    """Test the paused property."""
    sound.paused = True
    assert sound.paused is True
    assert sound._paused is True
    sound.paused = False
    assert sound.paused is False
    assert sound._paused is False


def test_destroy_generator(context: Context, sound: Sound) -> None:
    """Test that only the generator can be destroyed."""
    sound.destroy_generator()
    with raises(SynthizerError):
        sound.generator.destroy()
    assert sound.source is not None
    sound.source.destroy()


def test_set_gain(sound: Sound) -> None:
    """Test the set_gain method."""
    assert sound.gain == 1.0
    assert isinstance(sound.source, DirectSource)
    assert sound.source.gain == 1.0
    sound.set_gain(0.2)
    assert sound.gain == 0.2
    sleep(0.2)
    assert sound.source.gain == 0.2
    sound.set_gain(0.8)
    assert sound.gain == 0.8
    sleep(0.2)
    assert sound.source.gain == 0.8


def test_set_position(sound: Sound) -> None:
    """Test the set_position method."""
    assert sound.position is None
    assert isinstance(sound.source, DirectSource)
    sound.set_position(-1)
    assert sound.position == -1
    assert isinstance(sound.source, PannedSource)
    sleep(0.2)
    assert sound.source.position == -1
    sound.set_position(Point(3, 2, 1))
    assert sound.position == Point(3, 2, 1)
    assert isinstance(sound.source, Source3D)
    sleep(0.2)
    assert sound.source.position == (3, 2, 1)
    sound.set_position(None)
    assert sound.position is None
    assert isinstance(sound.source, DirectSource)
