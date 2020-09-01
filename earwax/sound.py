"""Provides the sound subsystem."""

from pathlib import Path
from random import choice
from typing import Dict, Optional, Tuple

from attr import attrs
from pyglet.clock import schedule_once
from synthizer import (Buffer, BufferGenerator, Context, DirectSource,
                       Generator, Source, SynthizerError)

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
    generator: Optional[Generator] = None, source: Optional[Source] = None
) -> Tuple[BufferGenerator, DirectSource]:
    """Plays the given sound file (or selects one from the given directory).

    :param ctx: The ``synthizer.Context`` to play through.

    :param path: Either the path to a single sound file, or a directory
        containing 1 or more sound files.

        If ``path`` is a directory, then a random sound file will be selected
        from it and played instead.
    """
    if path.is_dir():
        path = choice(list(path.iterdir()))
        return play_path(context, path)
    if generator is None:
        generator = BufferGenerator(context)
    generator.buffer = get_buffer('file', str(path))
    if source is None:
        source = DirectSource(context)
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


def schedule_generator_destruction(generator: BufferGenerator, multiplier: int = 2) -> None:
    """Using ``pyglet.clock.schedule_once``, schedules the given generator for
    destruction.

    :param generator: The generator to schedule for destruction.

    :param multiplier: The number to multiply the length of the buffer by.

        If this number is set to 1 (the obvious choice), the audio seems to stop prematurely.
    """

    def inner(dt: float) -> None:
        """Perform the destruction."""
        generator.destroy()

    schedule_once(inner, generator.buffer.get_length_in_seconds() * multiplier)
