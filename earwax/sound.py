"""Provides sound-related functions and classes."""

from pathlib import Path
from random import choice
from typing import Callable, Dict, List, Optional

from attr import Factory, attrib, attrs

try:
    from pyglet.clock import schedule_once
except ModuleNotFoundError:
    pass
try:
    from synthizer import (Buffer, BufferGenerator, Context, DirectSource,
                           Generator, GlobalFdnReverb, Source, Source3D,
                           StreamingGenerator)
except ModuleNotFoundError:
    (
        Buffer, BufferGenerator, Context, DirectSource, Generator, Source,
        Source3D, StreamingGenerator, GlobalFdnReverb
    ) = (None, None, None, None, None, None, None, None, None)

buffers: Dict[str, Buffer] = {}
OnDestroyFunction = Callable[[], None]


class SoundError(Exception):
    """The base exception for all sounds exceptions."""


class AlreadyDestroyed(SoundError):
    """This sound has already been destroyed."""


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


@attrs(auto_attribs=True)
class Sound:
    """The base class for all sounds.

    :ivar ~earwax.Sound.context: The synthizer context to connect to.

    :ivar ~earwax.Sound.source: The synthizer source to play through.

    :ivar ~earwax.Sound.generator: The sound generator.

    :ivar ~earwax.Sound.buffer: The buffer that feeds
        :attr:`~earwax.Sound.generator`.

        If this value is ``None``, then this sound is a stream.
    """

    context: Context
    source: Source
    generator: Generator
    buffer: Optional[Buffer]
    _valid: bool = Factory(lambda: True)

    @classmethod
    def from_stream(
        cls, context: Context, source: Source, protocol: str, path: str
    ) -> 'Sound':
        """Create a sound that streams from the given arguments.

        :param context: The synthizer context to use.

        :param source: The source to play through.

        :param protocol: The protocol argument for
            ``synthizer.StreamingGenerator``.

        :param path: The path parameter for ``synthizer.StreamingGenerator``.
        """
        generator: StreamingGenerator = StreamingGenerator(
            context, protocol, path
        )
        source.add_generator(generator)
        return cls(context, source, generator, None)

    @classmethod
    def from_path(
        cls, context: Context, source: Source, path: Path
    ) -> 'Sound':
        """Create a sound that plays the given path.

        :param context: The synthizer context to use.

        :param source: The synthizer source to play through.

        :param path: The path to play.

            If the given path is a directory, then a random file from that
            directory will be chosen.
        """
        if path.is_dir():
            return cls.from_path(context, source, choice(list(path.iterdir())))
        buffer: Buffer = get_buffer('file', str(path))
        generator: BufferGenerator = BufferGenerator(context)
        generator.buffer = buffer
        source.add_generator(generator)
        return cls(context, source, generator, buffer)

    @property
    def is_stream(self) -> bool:
        """Return ``True`` if this sound is being streamed.

        To determine whether or not a sound is being streamed, we check if
        :attr:`self.buffer <earwax.Sound.buffer>` is ``None``.
        """
        return self.buffer is None

    def destroy(self) -> None:
        """Destroy this sound.

        This method will destroy the attached :attr:`~earwax.Sound.generator`,
        but you must destroy the :attr:`~earwax.Sound.source` yourself.

        If this sound has already been destroyed, then
        :class:`~earwax.Sound.AlreadyDestroyed` will be raised.
        """
        if not self._valid:
            raise AlreadyDestroyed(self)
        self.generator.destroy()
        self._valid = False

    def _destroy(
        self, dt: float, on_destroy: Optional[OnDestroyFunction]
    ) -> None:
        """Call :meth:`self.destroy <earwax.Sound.destroy>`.

        This method will be called by pyglet. To schedule destruction, use the
        :meth:`~earwax.Sound.schedule_destruction` method.

        :param dt: The ``dt`` parameter expected by the pyglet schedule
            functions.

        :param on_destroy: A function to be called after this sound has been
            destroyed.
        """
        self.destroy()
        if on_destroy is not None:
            on_destroy()

    def schedule_destruction(
        self, on_destroy: Optional[OnDestroyFunction] = None
    ) -> None:
        """Schedule this sound for destruction.

        If this instance's :attr:`~earwax.Sound.buffer` attribute is ``None``,
        then ``RuntimeError`` will be raised.

        :param on_destroy: A function to be called after this sound has been
            destroyed.
        """
        if self.buffer is None:
            raise RuntimeError('This sound has no buffer to destroy.')
        schedule_once(
            self._destroy, self.buffer.get_length_in_seconds() * 2, on_destroy
        )

    def connect_reverb(self, reverb: GlobalFdnReverb) -> None:
        """Connect a reverb to the source of this sound.

        :param reverb: The reverb object to connect.
        """
        self.context.config_route(self.source, reverb)

    def restart(self) -> None:
        """Start this sound playing from the beginning."""
        self.generator.position = 0.0


@attrs(auto_attribs=True)
class SoundManager:
    """An object to hold sounds.

    :ivar ~earwax.SoundManager.context: The synthizer context to use.

    :ivar ~earwax.SoundManager.source: The synthizer source to play sounds
        through.

    :ivar ~earwax.SoundManager.should_loop: Whether or not to start new
        generators looping when using the various play methods.

    :ivar ~earwax.SoundManager.sounds: A list of sounds that are playing.

    :ivar ~earwax.SoundManager.gain: The gain of the connected
        :attr:`~earwax.SoundManager.source`.
    """

    context: Context
    source: Source
    should_loop: bool = Factory(bool)

    sounds: List[Sound] = attrib(Factory(list), init=False, repr=False)
    _gain: float = attrib(init=False)

    @_gain.default
    def get_default_gain(instance: 'SoundManager') -> float:
        """Get the default rain."""
        return instance.source.gain

    @property
    def gain(self) -> float:
        """Get the current gain."""
        return self._gain

    @gain.setter
    def gain(self, value: float) -> None:
        """Set the gain.

        :param value: The new gain.
        """
        self._gain = value
        self.source.gain = value

    def register_sound(self, sound: Sound) -> None:
        """Register a sound with this instance.

        :param sound: The sound to register.
        """
        self.sounds.append(sound)

    def remove_sound(self, sound: Sound) -> None:
        """Remove a sound from the :attr:`~earwax.SoundManager.sounds` list."""
        self.sounds.remove(sound)

    def destroy_sound(self, sound: Sound) -> None:
        """Destroy the given sound.

        This method will call the given sound's :meth:`~earwax.Sound.destroy`
        method, and remove it from the :attr:`~earwax.SoundManager.sounds`
        list.

        :param sound: The sound to be destroyed.
        """
        sound.destroy()
        self.remove_sound(sound)

    def destroy_all(self) -> None:
        """Destroy all the sounds associated with this manager."""
        while self.sounds:
            self.destroy_sound(self.sounds[0])

    def play_path(self, path: Path, schedule_destruction: bool) -> Sound:
        """Play a sound from a path.

        The resulting sound will be added to
        :attr:`~earwax.SoundManager.sounds` and returned.

        The created generator will have its ``looping`` property set to the
        value of :attr:`~earwax.SoundManager.should_loop`.

        :param path: The path to play.

        :param schedule_destruction: Whether or not to schedule the newly
            created sound for destruction when it has finished playing.
        """
        sound: Sound = Sound.from_path(self.context, self.source, path)
        sound.generator.looping = self.should_loop
        self.sounds.append(sound)
        if schedule_destruction:
            sound.schedule_destruction()
        return sound

    def play_stream(self, protocol: str, path: str) -> Sound:
        """Stream a sound.

        The resulting sound will be added to
        :attr:`~earwax.SoundManager.sounds` and returned.

        For full descriptions of the ``protocol``, and ``path`` arguments,
        check the synthizer documentation for ``StreamingGenerator``.

        :param protocol: The protocol to use.

        :param path: The path to use.
        """
        sound: Sound = Sound.from_stream(
            self.context, self.source, protocol, path
        )
        sound.generator.looping = self.should_loop
        self.sounds.append(sound)
        return sound


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
