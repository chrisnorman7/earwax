"""Provides sound-related functions and classes."""

from pathlib import Path
from random import choice
from typing import Dict, List, Optional, Tuple

from attr import Factory, attrib, attrs

try:
    from pyglet.clock import schedule_once
except ModuleNotFoundError:
    pass
try:
    from synthizer import (Buffer, BufferGenerator, Context, DirectSource,
                           Generator, Source, Source3D, StreamingGenerator)
except ModuleNotFoundError:
    (
        Buffer, BufferGenerator, Context, DirectSource, Generator, Source,
        Source3D, StreamingGenerator
    ) = (None, None, None, None, None, None, None, None)

buffers: Dict[str, Buffer] = {}

PositionTuple = Tuple[float, float, float]


def get_buffer(protocol: str, path: str) -> Buffer:
    """Get a Buffer instance.

    Buffers are cached in the buffers dictionary, so if there is already a
    buffer with the given protocol and path, it will be returned. Otherwise, a
    new buffer will be created, and added to the dictionary::

        assert isinstance(get_buffer('file', 'sound.wav'), synthizer.Buffer)
        # True.

    If you are going to destroy a buffer, make sure you remove it from the
    buffers dictionary.

    At present, both arguments are passed to ``synthizer.Buffer.from_stream``.

    :param protocol: One of the protocols from `Synthizer
        <https://synthizer.github.io/>`__.

        As far as I know, currently only ``'file'`` works.

    :param path: The path to the socket data.
    """
    url: str = f'{protocol}://{path}'
    if url not in buffers:
        buffers[url] = Buffer.from_stream(protocol, path)
    return buffers[url]


def play_path(
    context: Context, path: Path,
    generator: Optional[Generator] = None, source: Optional[Source] = None,
    position: Optional[PositionTuple] = None
) -> Tuple[BufferGenerator, Source]:
    """Plays the given sound file (or selects one from the given directory).

    :param ctx: The ``synthizer.Context`` to play through.

    :param path: Either the path to a single sound file, or a directory
        containing 1 or more sound files.

        If ``path`` is a directory, then a random sound file will be selected
        from it and played instead.

    :param generator: A ready-to-use ``BufferGenerator``.

        If ``None`` is provided, then a new ``BufferGenerator`` instance will
        be created and returned.

    :param source: A ready-to-use source.

        If ``None`` is provided, an appropriate ``Source`` instance will be
        used.

    :param position: The position the new sound should play at.

        If ``None`` is provided, then no position will be set. If ``source`` is
        ``None``, then a ``DirectSource`` object will be created for you.

        If position is not ``None``, then it will be applied to the source. If
        ``source`` is ``None``, then a ``Source3D`` instance will be created.
    """
    if path.is_dir():
        path = choice(list(path.iterdir()))
        return play_path(
            context, path, generator=generator, source=source,
            position=position
        )
    if generator is None:
        generator = BufferGenerator(context)
    generator.buffer = get_buffer('file', str(path))
    if source is None:
        if position is None:
            source = DirectSource(context)
        else:
            source = Source3D(context)
    if isinstance(source, Source3D) and position is not None:
        source.position = position
    source.add_generator(generator)
    return (generator, source)


def stream_sound(
    context: Context, protocol: str, path: str,
    source: Optional[Source] = None, position: Optional[PositionTuple] = None
) -> Tuple[StreamingGenerator, Source]:
    """Stream a sound.

    Using this method, you can stream a sound using Synthizer's streaming API.

    :param context: The synthizer context to play through.

    :param protocol: The protocol parameter to pass to
        ``synthizer.StreamingGenerator``.

    :param path: The path parameter to pass to
        ``synthizer.StreamingGenerator``.

    :param source: A ready-to-use source.

        If ``None`` is provided, an appropriate ``Source`` instance will be
        used.

    :param position: The position the new sound should play at.

        If ``None`` is provided, then no position will be set. If ``source`` is
        ``None``, then a ``DirectSource`` object will be created for you.

        If position is not ``None``, then it will be applied to the source. If
        ``source`` is ``None``, then a ``Source3D`` instance will be created.
    """
    generator: StreamingGenerator = StreamingGenerator(context, protocol, path)
    if source is None:
        if position is None:
            source = DirectSource(context)
        else:
            source = Source3D(context)
    if isinstance(source, Source3D) and position is not None:
        source.position = position
    source.add_generator(generator)
    return (generator, source)


@attrs(auto_attribs=True)
class SimpleInterfaceSoundPlayer:
    """An object which plays a sound whenever its play method is called.

    The same sound will be used, and it will be restarted on each call to play.

    No panning or fx are applied.

    Here is a basic example::

        from time import sleep
        from synthizer import Context, BufferGenerator, initialize, shutdown
        from earwax.sound import get_buffer, SimpleInterfaceSoundPlayer
        initialize()
        c = Context()
        g = BufferGenerator(c)
        b = get_buffer('file', 'sound.wav')
        g.buffer = b
        p = SimpleInterfaceSoundPlayer(c, g)
        p.play()
        sleep(2)
        shutdown()

    :ivar ~earwax.SimpleInterfaceSoundPlayer.context: The audio context to use.

    :ivar ~earwax.SimpleInterfaceSoundPlayer.generator: The generator to use.

    :ivar ~earwax.SimpleInterfaceSoundPlayer.source: The source to play
        through.

    :ivar ~earwax.SimpleInterfaceSoundPlayer.gain: The gain to set on
        :attr:`self.source <earwax.SimpleInterfaceSoundPlayer.source>`, if no
        source is provided when constructing instances of this class.
    """

    context: Context
    generator: Generator
    source: Optional[Source] = None
    gain: float = 1.0

    def play(self) -> None:
        """Play the sound that is attached to this instance.

        Plays :attr:`self.generator
        <earwax.SimpleInterfaceSoundPlayer.generator>`.
        """
        if self.source is None:
            self.source = DirectSource(self.context)
            self.source.gain = self.gain
            self.source.add_generator(self.generator)
        self.generator.position = 0


@attrs(auto_attribs=True)
class AdvancedInterfaceSoundPlayer:
    """An interface player that can play any sound you throw at it.

    To play a sound, pass a path to the
    :meth:`~earwax.AdvancedInterfaceSoundPlayer.play_path` method::

        from pathlib import Path
        from time import sleep
        from synthizer import Context, initialized
        from earwax import AdvancedInterfaceSoundPlayer
        with initialized():
            c = Context()
            p = AdvancedInterfaceSoundPlayer(c)
            p.play_path(Path('sound.wav'))
            sleep(2)
            p.play_path(Path('move.wav'))
            sleep(2)

    :ivar ~earwax.AdvancedInterfaceSoundPlayer.play_files: If True, then files
        will be played.

    :ivar ~earwax.AdvancedInterfaceSoundPlayer.play_directories: If True, then
        a random file will be picked from any directory that is passed to the
        :meth:`~earwax.AdvancedInterfaceSoundPlayer.play_path` method.
    """

    context: Context
    play_files: bool = True
    play_directories: bool = False
    generator: BufferGenerator = attrib()

    @generator.default
    def get_generator(
        instance: 'AdvancedInterfaceSoundPlayer'
    ) -> BufferGenerator:
        """Return the default value.

        Makes a ``BufferGenerator`` instance, bound to :attr:`self.context
        <earwax.AdvancedInterfaceSoundPlayer.context>`.

        :param instance: The instance to use.
        """
        return BufferGenerator(instance.context)

    gain: float = 1.0
    source: Source = attrib()

    @source.default
    def get_source(instance: 'AdvancedInterfaceSoundPlayer') -> Source:
        """Return a default value.

        Gets a ``DirectSource`` instance, bound to :attr:`self.context
        <earwax.AdvancedInterfaceSoundPlayer>`, with a gain value of
        :attr:`self.gain <earwax.AdvancedInterfaceSoundPlayer>`.
        """
        s: DirectSource = DirectSource(instance.context)
        s.gain = instance.gain
        return s

    def play_path(self, path: Path) -> None:
        """Play the given path.

        If :attr:`self.play_directories
        <earwax.AdvancedInterfaceSoundPlayer.play_directories>` evaluates to
        True, and the given path represents a directory, play a random file
        from that directory. Otherwise, if :meth:`self.play_files
        <earwax.AdvancedInterfaceSoundPlayer.play_files>` evaluates to True,
        play the given path.
        """
        if path.is_dir():
            if not self.play_directories:
                return
        elif path.is_file():
            if not self.play_files:
                return
        else:
            raise NotImplementedError(f'No clue how to play {path}.')
        self.buffer, self.source = play_path(
            self.context, path, generator=self.generator, source=self.source
        )


def schedule_generator_destruction(
    generator: BufferGenerator, multiplier: int = 2
) -> None:
    """Schedule a generator for destruction.

    Uses ``pyglet.clock.schedule_once``, schedules ``generator.destroy``.

    :param generator: The generator to schedule for destruction.

    :param multiplier: The number to multiply the length of the buffer by.

        If this number is set to 1 (which would have been the obvious choice),
        the audio seems to stop prematurely.
    """

    def inner(dt: float) -> None:
        """Perform the destruction."""
        generator.destroy()

    schedule_once(inner, generator.buffer.get_length_in_seconds() * multiplier)


def play_and_destroy(*args, **kwargs) -> None:
    """Play a path, cleaning up the generator afterwards.

    Calls :meth:`~earwax.play_path` with the given ``args`` and ``kwargs``,
    then schedules the returned generator for destruction using
    :meth:`~earwax.schedule_generator_destruction`.

    :param args: The positional arguments to pass to ``play_path``.

    :param kwargs: The keyword arguments to pass to ``play_path``.
    """
    generator: BufferGenerator
    source: Source
    generator, source = play_path(*args, **kwargs)
    schedule_generator_destruction(generator)


def play_paths(ctx: Context, paths: List[Path], gap: float = 0.1) -> None:
    """Play every path in the list, one after another.

    :param paths: The paths to play in order.

    :param gap: The number of seconds to add to the scheduling.
    """
    delay: Optional[float] = None
    p: Path
    for p in paths:
        buffer: Buffer = get_buffer('file', str(p))
        duration: float = buffer.get_length_in_seconds()

        def inner(dt: float) -> None:
            """Actually play the path."""
            play_and_destroy(ctx, p)

        if delay is None:
            delay = 0
            inner(0.0)
        else:
            delay += duration + gap
            schedule_once(inner, delay)


@attrs(auto_attribs=True, frozen=True)
class BufferDirectory:
    """An object which holds a directory of ``synthizer.Buffer`` instances.

    For example::

        b: BufferDirectory = BufferDirectory(
            Path('sounds/weapons/cannons'), glob='*.wav'
        )
        # Get a random cannon buffer:
        print(b.random_buffer())
        # Get a random fully qualified path from the directory.
        print(b.random_path())

    You can select single buffer instances from the
    :attr:`~earwax.BufferDirectory.buffers` dictionary, or a random buffer with
    the :meth:`~earwax.BufferDirectory.random_buffer` method.

    You can select single ``Path`` instances from the
    :attr:`~earwax.BufferDirectory.paths` dictionary, or a random path with the
    :meth:`~earwax.BufferDirectory.random_path` method.

    :ivar ~earwax.BufferDirectory.path: The path to load audio files from.

    :ivar ~earwax.BufferDirectory.glob: The glob to use when loading files.

    :ivar ~earwax.BufferDirectory.buffers: A dictionary of of ``filename:
        Buffer`` pairs.

    :ivar ~earwax.BufferDirectory.paths: A dictionary of ``filename: Path``
        pairs.
    """

    path: Path

    glob: Optional[str] = None

    paths: Dict[str, Path] = attrib(init=False, default=Factory(dict))

    buffers: Dict[str, Buffer] = attrib(init=False)

    @buffers.default
    def buffers_default(instance: 'BufferDirectory') -> Dict[str, Path]:
        """Return the default value.

        Populates the :attr:`~earwax.BufferDirectory.buffers` and
        :attr:`~earwax.BufferDirectory.paths` dictionaries.
        """
        g: Generator[Path]
        if instance.glob is None:
            g = instance.path.iterdir()
        else:
            g = instance.path.glob(instance.glob)
        d: Dict[str, Buffer] = {}
        p: Path
        for p in g:
            p = p.resolve()
            instance.paths[p.name] = p
            d[p.name] = get_buffer('file', str(p))
        return d

    def random_path(self) -> Path:
        """Return a random path.

        Returns a random path from :attr:`self.paths
        <earwax.BufferDirectory.paths>`.
        """
        return choice(list(self.paths.values()))

    def random_buffer(self) -> Buffer:
        """Return a random buffer.

        Returns a random buffer from :attr:`self.buffers
        <earwax.BufferDirectory.buffers>`.
        """
        return choice(list(self.buffers.values()))
