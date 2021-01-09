"""Provides sound-related functions and classes."""

from concurrent.futures import Executor
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
                           StreamingGenerator, SynthizerError)
except ModuleNotFoundError:
    (
        Buffer, BufferGenerator, Context, DirectSource, Generator, Source,
        Source3D, StreamingGenerator, GlobalFdnReverb
    ) = (None, None, None, None, None, None, None, None, None)
    SynthizerError = Exception

OnDestroyFunction = Callable[[], None]


@attrs(auto_attribs=True)
class BufferCache:
    """A cache for buffers.

    :ivar ~earwax.BufferCache.max_size: The maximum size (in bytes) the cache
        will be allowed to grow before pruning.

    :ivar ~earwax.BufferCache.buffer_uris: The URIs of the buffers that are
        loaded. Least recently used first.

    :ivar ~earwax.BufferCache.buffers: The loaded buffers.

    :ivar ~earwax.BufferCache.current_size: The current size of the cache.
    """

    max_size: int

    buffer_uris: List[str] = attrib(
        default=Factory(list), init=False, repr=False
    )
    buffers: Dict[str, Buffer] = attrib(
        default=Factory(dict), init=False, repr=False
    )
    current_size: int = attrib(default=Factory(int), init=False)

    def get_size(self, buffer: Buffer) -> int:
        """Return the size of the provided buffer.

        :param buffer: The buffer to get the size of.
        """
        return buffer.get_channels() * buffer.get_length_in_samples() * 2

    def get_buffer(self, protocol: str, path: str) -> Buffer:
        """Load and return a Buffer instance.

        Buffers are cached in the :attr:`~earwax.BufferCache.buffers`
        dictionary, so if there is already a buffer with the given protocol and
        path, it will be returned. Otherwise, a new buffer will be created, and
        added to the dictionary::

            cache: BufferCache = BufferCache(1024 ** 2 * 512)  # 512 MB max.
            assert isinstance(
                cache.get_buffer('file', 'sound.wav'), synthizer.Buffer
            )
            # True.
            # Now it is cached:
            assert cache.get_buffer(
                'file', 'sound.wav'
            ) is cache.get_buffer(
                'file', 'sound.wav'
            )
            # True.

        If getting a new buffer would grow the cache past the point of
        :attr:`~earwax.BufferCache.max_size`, the least recently used buffer
        will be removed and destroyed.

        It is not recommended that you destroy buffers yourself. Let the cache
        do that for you.

        At present, both arguments are passed to
        ``synthizer.Buffer.from_stream``.

        :param protocol: One of the protocols supported by `Synthizer
            <https://synthizer.github.io/>`__.

            As far as I know, currently only ``'file'`` works.

        :param path: The path to whatever data your buffer will contain.
        """
        uri: str = f'{protocol}://{path}'
        if uri not in self.buffers:
            # Firstly load the buffer.
            buffer: Buffer = Buffer.from_stream(protocol, path)
            self.buffer_uris.insert(0, uri)
            self.buffers[uri] = buffer
            self.current_size += self.get_size(buffer)
            self.prune_buffers()
        return self.buffers[uri]

    def prune_buffers(self) -> None:
        """Prune old buffers.

        This function will keep going, until either there is only ` buffer
        left, or :attr:`~earwax.BufferCache.current_size` has shrunk to less
        than :attr:`~earwax.BufferCache.max_size`.
        """
        while self.current_size > self.max_size and len(self.buffer_uris) > 1:
            self.pop_buffer().destroy()

    def pop_buffer(self) -> Buffer:
        """Remove and return the least recently used buffer."""
        uri: str = self.buffer_uris.pop()
        buffer: Buffer = self.buffers.pop(uri)
        self.current_size -= self.get_size(buffer)
        return buffer

    def destroy_all(self) -> None:
        """Destroy all the buffers cached by this instance."""
        while self.buffer_uris:
            self.pop_buffer().destroy()
        self.current_size = 0  # Should be anyway.


class SoundError(Exception):
    """The base exception for all sounds exceptions."""


class AlreadyDestroyed(SoundError):
    """This sound has already been destroyed."""


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
    _paused: bool = False

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
        cls, context: Context, source: Source, buffer_cache: BufferCache,
        path: Path
    ) -> 'Sound':
        """Create a sound that plays the given path.

        :param context: The synthizer context to use.

        :param source: The synthizer source to play through.

        :param cache: The buffer cache to load buffers from.

        :param path: The path to play.

            If the given path is a directory, then a random file from that
            directory will be chosen.
        """
        if path.is_dir():
            return cls.from_path(
                context, source, buffer_cache, choice(list(path.iterdir()))
            )
        buffer: Buffer = buffer_cache.get_buffer('file', str(path))
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

    @property
    def paused(self) -> bool:
        """Return whether or not this sound is paused."""
        return self._paused

    @paused.setter
    def paused(self, value: bool) -> None:
        """Set the paused state."""
        if value:
            self.pause()
        else:
            self.play()

    def pause(self) -> None:
        """Pause this sound."""
        self._paused = True
        self.generator.pause()

    def play(self) -> None:
        """Resumes this sound after a call to :meth:`~earwax.Sound.pause`."""
        self._paused = False
        self.generator.play()

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


class SoundManagerError(Exception):
    """The base class for all sound manager errors."""


class NoCache(SoundManagerError):
    """This sound manager was created with no cache."""


@attrs(auto_attribs=True)
class SoundManager:
    """An object to hold sounds.

    :ivar ~earwax.SoundManager.context: The synthizer context to use.

    :ivar ~earwax.SoundManager.source: The synthizer source to play sounds
        through.

    :ivar ~earwax.SoundManager.should_loop: Whether or not to start new
        generators looping when using the various play methods.

    :ivar ~earwax.SoundManager.cache: The buffer cache to get buffers from.

    :ivar ~earwax.SoundManager.sounds: A list of sounds that are playing.

    :ivar ~earwax.SoundManager.gain: The gain of the connected
        :attr:`~earwax.SoundManager.source`.
    """

    context: Context
    source: Source
    should_loop: bool = Factory(bool)
    buffer_cache: Optional[BufferCache] = None

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
        if self.buffer_cache is None:
            raise NoCache(self)
        sound: Sound = Sound.from_path(
            self.context, self.source, self.buffer_cache, path
        )
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

    def __del__(self) -> None:
        """Stop all sounds."""
        try:
            self.source.destroy()
        except (SynthizerError, AttributeError):
            pass


@attrs(auto_attribs=True, frozen=True)
class BufferDirectory:
    """An object which holds a directory of ``synthizer.Buffer`` instances.

    For example::

        b: BufferDirectory = BufferDirectory(
            cache, Path('sounds/weapons/cannons'), glob='*.wav'
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

    :ivar ~earwax.BufferDirectory.cache: The buffer cache to use.

    :ivar ~earwax.BufferDirectory.path: The path to load audio files from.

    :ivar ~earwax.BufferDirectory.glob: The glob to use when loading files.

    :ivar ~earwax.BufferDirectory.buffers: A dictionary of of ``filename:
        Buffer`` pairs.

    :ivar ~earwax.BufferDirectory.paths: A dictionary of ``filename: Path``
        pairs.
    """

    buffer_cache: BufferCache
    path: Path
    glob: Optional[str] = None

    thread_pool: Optional[Executor] = None

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

        def inner(p: Path) -> None:
            p = p.resolve()
            instance.paths[p.name] = p
            d[p.name] = instance.buffer_cache.get_buffer('file', str(p))

        map_generator: Generator[None, None, None]
        if instance.thread_pool is None:
            map_generator = map(inner, g)
        else:
            map_generator = instance.thread_pool.map(inner, g)
        list(map_generator)
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
