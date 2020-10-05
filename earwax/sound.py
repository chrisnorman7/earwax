"""Provides the sound subsystem."""

from pathlib import Path
from random import choice
from typing import Dict, List, Optional, Tuple

from attr import attrs
from pyglet.clock import schedule_once
from synthizer import (Buffer, BufferGenerator, Context, DirectSource,
                       Generator, Source, Source3D, SynthizerError)

buffers: Dict[str, Buffer] = {}


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
    position: Optional[Tuple[float, float, float]] = None
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
        return play_path(context, path)
    if generator is None:
        generator = BufferGenerator(context)
    generator.buffer = get_buffer('file', str(path))
    if source is None:
        if position is None:
            source = DirectSource(context)
        else:
            source = Source3D(context)
    if position is not None:
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
    """

    context: Context
    generator: Generator
    source: Source = None

    def play(self) -> None:
        """Play :attr:`self.generator
        <earwax.SimpleInterfaceSoundPlayer.generator>`."""
        if self.source is None:
            self.source = DirectSource(self.context)
            self.source.add_generator(self.generator)
        self.generator.position = 0

    def __del__(self) -> None:
        """Destroy the source and the generator."""
        try:
            if getattr(self, 'generator', None) is not None:
                self.generator.destroy()
            if getattr(self, 'source', None) is not None:
                self.source.destroy()
        except SynthizerError:
            pass  # They're already gone.


class AdvancedInterfaceSoundPlayer(SimpleInterfaceSoundPlayer):
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

    play_files: bool
    play_directories: bool

    def __init__(
        self, context: Context, play_files: bool = True,
        play_directories: bool = False
    ):
        self.play_files = play_files
        self.play_directories = play_directories
        super().__init__(context, BufferGenerator(context))

    def play_path(self, path: Path) -> None:
        """If :attr:`self.play_directories
        <earwax.AdvancedInterfaceSoundPlayer.play_directories>` evaluates to
        True, and the given path represents a directory, play a random file
        from that directory. Otherwise, if :meth:`self.play_files
        <earwax.AdvancedInterfaceSoundPlayer.play_files>` evaluates to True,
        play the given path."""
        if self.generator is None:
            self.generator = BufferGenerator(self.context)
        if self.source is None:
            self.source = DirectSource(self.context)
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
    """Using ``pyglet.clock.schedule_once``, schedules ``generator.destroy``.

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
    """Calls :meth:`~earwax.play_path` with the given ``args`` and ``kwargs``,
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


class BufferDirectory:
    """An object which holds a directory of ``synthizer.Buffer`` instances.

    You can select single buffer instances from the
    :attr:`~earwax.BufferDirectory.buffers` dictionary, or a random buffer with
    the :meth:`~earwax.BufferDirectory.random_buffer` method.

    :ivar ~earwax.BufferDirectory.buffers: A dictionary of of ``filename:
        Buffer`` pairs.
    """

    buffers: Dict[str, Buffer]

    def __init__(self, path: Path, glob: Optional[str] = None) -> None:
        """Load a directory of files.

        :param path: The directory to load from.

        :param glob: The glob to use.

            If this value is ``None``, then every file will be loaded.
        """
        assert path.is_dir(), ('Invalid directory: %r.' % path)
        g: Generator[Path]
        if glob is None:
            g = path.iterdir()
        else:
            g = path.glob(glob)
        self.buffers = {}
        p: Path
        for p in g:
            p = p.resolve()
            self.buffers[p.name] = get_buffer('file', p.name)

    def random_buffer(self) -> Buffer:
        """Returns a random buffer from :attr:`self.buffers
        <earwax.BufferDirectory.buffers>`.
        """
        return choice(list(self.buffers.values()))
