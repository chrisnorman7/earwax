"""Provides sound-related functions and classes."""

from concurrent.futures import Executor
from pathlib import Path
from random import choice
from typing import (Any, Callable, Dict, Generator, Iterator, List, Optional,
                    Union)

from attr import Factory, attrib, attrs

from .utils import random_file as _random_file

try:
    from synthizer import Buffer, BufferGenerator, Context, DirectSource
    from synthizer import Generator as SynthizerGenerator
    from synthizer import (GlobalFdnReverb, PannedSource, PannerStrategy,
                           Source, Source3D, StreamingGenerator,
                           SynthizerError)
except ModuleNotFoundError:
    (
        Buffer, BufferGenerator, Context, DirectSource, SynthizerGenerator,
        GlobalFdnReverb, PannedSource, PannerStrategy, Source, Source3D,
        StreamingGenerator
    ) = (
        object, object, object, object, object, object, object, object, object,
        object, object
    )
    SynthizerError = Exception

from .point import Point

SoundEventType = Callable[['Sound'], None]
PositionType = Optional[Union[float, Point]]


@attrs(auto_attribs=True)
class BufferCache:
    """A cache for buffers.

    :ivar ~earwax.BufferCache.max_size: The maximum size (in bytes) the cache
        will be allowed to grow before pruning.

        For reference, 1 KB is ``1024``,  1 MB is ``1024 ** 2``, and 1 GB is
        ``1024 ** 3``.

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

    def get_uri(self, protocol: str, path: str) -> str:
        """Return a URI for the given protocol and path.

        This meth is used by :meth:`~earwax.BufferCache.get_buffer`.
        :param protocol: The protocol to use.

        :param path: The path to use.
        """
        return f'{protocol}://{path}'

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
        uri: str = self.get_uri(protocol, path)
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

    :ivar ~earwax.Sound.generator: The sound generator.

    :ivar ~earwax.Sound.buffer: The buffer that feeds
        :attr:`~earwax.Sound.generator`.

        If this value is ``None``, then this sound is a stream.

    :ivar ~earwax.Sound.gain: The gain of the new sound.

    :ivar ~earwax.Sound.loop: Whether or not this sound should loop.

    :ivar ~earwax.Sound.position: The position of this sound.

        If this value is ``None``, this sound will not be panned.

        If this value is an :class:`earwax.Point` value, then this sound
        will be a 3d sound, and the position of its
        :attr:`~earwax.Sound.source` will be set to the coordinates of the
        given point.

        If this value is a number, this sound will be panned in 2d, and
        the value will be a panning scalar, which should range between
        ``-1.0`` (hard left), and ``1.0`` (hard right).

    :ivar ~earwax.Sound.on_destroy: A function to be called when this sound is
        destroyed.

    :ivar ~earwax.Sound.on_finished: A function to be called when this sound
        has finished playing, and :attr:`~earwax.Sound.looping` evaluates to
        ``False``.

        The timing of this event should not be relied upon.

    :ivar ~earwax.Sound.on_looped: A function to be called each time this sound
        loops.

        The timing of this event should not be relied upon.

    :ivar ~earwax.Sound.keep_around: Whether or not this sound should be kept
        around when it has finished playing.

        If this value evaluates to ``True``, it is the same as setting the
        :attr:`~earwax.Sound.on_finished` attribute to
        :meth:`~earwax.Sound.destroy`.

    :ivar ~earwax.Sound.source: The synthizer source to play through.
    """

    context: Context
    generator: SynthizerGenerator
    buffer: Optional[Buffer] = None
    gain: float = 1.0
    looping: bool = False
    position: PositionType = None
    reverb: Optional[GlobalFdnReverb] = None
    on_destroy: Optional[SoundEventType] = None
    on_finished: Optional[SoundEventType] = None
    on_looped: Optional[SoundEventType] = None
    keep_around: bool = Factory(bool)
    _destroyed: bool = attrib(default=Factory(bool), init=False)
    _paused: bool = attrib(default=Factory(bool), init=False)
    source: Optional[Source] = attrib(
        default=Factory(type(None)), init=False, repr=False
    )

    def __attrs_post_init__(self) -> None:
        """Finish setting up this sound."""
        self.generator.looping = self.looping
        self.generator.set_userdata(self)
        self.reset_source()

    @classmethod
    def from_stream(
        cls, context: Context, protocol: str, path: str, **kwargs
    ) -> 'Sound':
        """Create a sound that streams from the given arguments.

        :param context: The synthizer context to use.

        :param protocol: The protocol argument for
            ``synthizer.StreamingGenerator``.

        :param path: The path parameter for ``synthizer.StreamingGenerator``.
        """
        generator: StreamingGenerator = StreamingGenerator(
            context, protocol, path
        )
        return cls(context, generator, None, **kwargs)

    @classmethod
    def from_path(
        cls, context: Context, buffer_cache: BufferCache, path: Path, **kwargs
    ) -> 'Sound':
        """Create a sound that plays the given path.

        :param context: The synthizer context to use.

        :param cache: The buffer cache to load buffers from.

        :param path: The path to play.

            If the given path is a directory, then a random file from that
            directory will be chosen.

        :parm kwargs: Extra keyword arguments to pass to the
            :attr:`~earwax.Sound` constructor.
        """
        path = _random_file(path)
        buffer: Buffer = buffer_cache.get_buffer('file', str(path))
        generator: BufferGenerator = BufferGenerator(context)
        generator.buffer = buffer
        return cls(context, generator, buffer, **kwargs)

    @property
    def is_stream(self) -> bool:
        """Return ``True`` if this sound is being streamed.

        To determine whether or not a sound is being streamed, we check if
        :attr:`self.buffer <earwax.Sound.buffer>` is ``None``.
        """
        return self.buffer is None

    @property
    def destroyed(self) -> bool:
        """Return whether or not this sound has been destroyed."""
        return self._destroyed

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

        def on_destroy(self) -> None:
            """Handle this sound being destroyed."""
            pass

    def check_destroyed(self) -> None:
        """Do nothing if this sound has not yet been destroyed.

        If it has been destroyed, :class:`~earwax.AlreadyDestroyed` will be
        raised.
        """
        if self._destroyed:
            raise AlreadyDestroyed(self)

    def reset_source(self) -> Source:
        """Return an appropriate source."""
        self.check_destroyed()
        if self.source is not None:
            self.source.destroy()
            self.source = None
        source: Source
        if self.position is None:
            source = DirectSource(self.context)
        else:
            if isinstance(self.position, Point):
                source = Source3D(self.context)
                source.position = self.position.coordinates
            elif isinstance(self.position, (float, int)):
                source = PannedSource(self.context)
                source.panning_scalar = self.position
            else:
                raise RuntimeError(f'Invalid position: {self.position}')
        source.add_generator(self.generator)
        source.gain = self.gain
        self.source = source
        if self.reverb is not None:
            self.connect_reverb(self.reverb)

    def set_position(self, position: PositionType) -> None:
        """Change the position of this sound.

        If the provided position is of a different type than the :attr:`current
        one <earwax.Sound.position>`, then the underlying
        :attr:`~earwax.Sound.source` object will need to changee. This will
        probably cause audio stuttering.

        :param position: The new position.
        """
        old_position: PositionType = self.position
        self.position = position
        if not isinstance(position, type(old_position)):
            self.reset_source()
        elif isinstance(position, Point):
            assert isinstance(self.source, Source3D)
            self.source.position = position.coordinates
        elif isinstance(position, (float, int)):
            assert isinstance(self.source, PannedSource)
            self.source.panning_scalar = position
        else:
            assert isinstance(self.source, DirectSource)
            assert position is None

    def set_gain(self, gain: float) -> None:
        """Change the gain of this sound.

        :param gain: The new gain value.
        """
        self.gain = gain
        if self.source is not None:
            self.source.gain = gain

    def set_looping(self, looping: bool) -> None:
        """Set whether or not this sound should loop.

        :param looping: Whether or not to loop.
        """
        self.looping = looping
        self.generator.looping = looping

    def pause(self) -> None:
        """Pause this sound."""
        self.check_destroyed()
        self._paused = True
        self.generator.pause()

    def play(self) -> None:
        """Resumes this sound after a call to :meth:`~earwax.Sound.pause`."""
        self.check_destroyed()
        self._paused = False
        self.generator.play()

    def destroy_generator(self) -> None:
        """Destroy the :attr:`~earwax.Sound.generator`.

        This method will leave the :attr:`~earwax.Sound.source` intact, and
        will raise :class:`~earwax.AlreadyDestroyed` if the generator is still
        valid.
        """
        self.check_destroyed()
        self.generator.destroy()

    def destroy_source(self) -> None:
        """Destroy the attached :attr:`~earwax.Sound.source`.

        If the source has already been destroyed,
        :class:`~earwax.AlreadyDestroyed` will be raised.
        """
        self.check_destroyed()
        assert self.source is not None
        self.source.destroy()
        self.source = None

    def destroy(self) -> None:
        """Destroy this sound.

        This method will destroy the attached :attr:`~earwax.Sound.generator`
        and :attr:`~earwax.Sound.source`.

        If this sound has already been destroyed, then
        :class:`~earwax.Sound.AlreadyDestroyed` will be raised.
        """
        self.disconnect_reverb()
        self.destroy_generator()
        if self.source is not None:
            self.destroy_source()
        self._destroyed = True
        if self.on_destroy is not None:
            self.on_destroy(self)

    def connect_reverb(self, reverb: GlobalFdnReverb) -> None:
        """Connect a reverb to the source of this sound.

        :param reverb: The reverb object to connect.
        """
        self.check_destroyed()
        self.reverb = reverb
        self.context.config_route(self.source, reverb)

    def disconnect_reverb(self) -> None:
        """Disconnect the connected :attr:`~earwax.Sound.reverb` object."""
        if self.reverb is not None and self.source is not None:
            try:
                self.context.remove_route(self.source, self.reverb)
            except SynthizerError:
                pass
            self.reverb = None

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

    :ivar ~earwax.SoundManager.cache: The buffer cache to get buffers from.

    :ivar ~earwax.SoundManager.name: An optional name to set this manager aside
        from other sound managers when debugging.

    :ivar ~earwax.SoundManager.default_gain: The default
        :attr:`~earwax.Sound.gain` attribute for sounds created by this
        manager.

    :ivar ~earwax.SoundManager.default_looping: The default
        :attr:`~earwax.Sound.looping` attribute for sounds created by this
        manager.

    :ivar ~earwax.SoundManager.default_position: The default
        :attr:`~earwax.Sound.position` attribute for sounds created by this
        manager.

    :ivar ~earwax.SoundManager.default_reverb: The default
        :attr:`~earwax.Sound.reverb` attribute for sounds created by this
        manager.

    :ivar ~earwax.SoundManager.sounds: A list of sounds that are playing.
    """

    context: Context = attrib(repr=False)
    buffer_cache: Optional[BufferCache] = attrib(
        default=Factory(type(None)), repr=False
    )

    name: str = 'Untitled sound manager'
    default_gain: float = 1.0
    default_looping: bool = False
    default_position: PositionType = None
    default_reverb: Optional[GlobalFdnReverb] = None

    sounds: List[Sound] = attrib(Factory(list), init=False, repr=False)

    def register_sound(self, sound: Sound) -> None:
        """Register a sound with this instance.

        :param sound: The sound to register.
        """
        self.sounds.append(sound)
        if sound.on_destroy is None:
            sound.on_destroy = self.remove_sound

    def remove_sound(self, sound: Sound) -> None:
        """Remove a sound from the :attr:`~earwax.SoundManager.sounds` list.

        :param sound: The sound that will be removed
        """
        self.sounds.remove(sound)
        if sound.on_destroy == self.remove_sound:
            sound.on_destroy = None

    def destroy_all(self) -> None:
        """Destroy all the sounds associated with this manager."""
        while self.sounds:
            try:
                self.sounds[0].destroy()
            except AlreadyDestroyed:
                pass  # Someone else got there first.

    def update_kwargs(self, kwargs: Dict[str, Any]) -> None:
        """Update the passed kwargs with the defaults from this manager.

        :param kwargs: The dictionary of keyword arguments to update.

            The ``setdefault`` method will be used with each of the default
            values from this object..
        """
        kwargs.setdefault('gain', self.default_gain)
        kwargs.setdefault('looping', self.default_looping)
        kwargs.setdefault('position', self.default_position)
        kwargs.setdefault('reverb', self.default_reverb)
        kwargs.setdefault('on_destroy', self.remove_sound)

    def play_path(self, path: Path, /, **kwargs) -> Sound:
        """Play a sound from a path.

        The resulting sound will be added to
        :attr:`~earwax.SoundManager.sounds` and returned.

        :param path: The path to play.

        :param kwargs: Extra keyword arguments to pass to the constructor of
            :class:`earwax.Sound`.

            This value will be updated by the
            :meth:`~earwax.SoundManager.update_kwargs` method.
        """
        if self.buffer_cache is None:
            raise NoCache(self)
        self.update_kwargs(kwargs)
        sound: Sound = Sound.from_path(
            self.context, self.buffer_cache, path, **kwargs
        )
        self.sounds.append(sound)
        return sound

    def play_stream(self, protocol: str, path: str, /, **kwargs) -> Sound:
        """Stream a sound.

        The resulting sound will be added to
        :attr:`~earwax.SoundManager.sounds` and returned.

        For full descriptions of the ``protocol``, and ``path`` arguments,
        check the synthizer documentation for ``StreamingGenerator``.

        :param protocol: The protocol to use.

        :param path: The path to use.

        :param kwargs: Extra keyword arguments to pass to the constructor of
            the :class:`earwax.Sound` class.

            This value will be updated by the
            :meth:`~earwax.SoundManager.update_kwargs` method.
        """
        self.update_kwargs(kwargs)
        sound: Sound = Sound.from_stream(
            self.context, protocol, path, **kwargs
        )
        self.sounds.append(sound)
        return sound


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
    def buffers_default(instance: 'BufferDirectory') -> Dict[str, Buffer]:
        """Return the default value.

        Populates the :attr:`~earwax.BufferDirectory.buffers` and
        :attr:`~earwax.BufferDirectory.paths` dictionaries.
        """
        g: Generator[Path, None, None]
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

        map_generator: Iterator[None]
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
