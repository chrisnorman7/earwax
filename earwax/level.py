"""Provides classes for working with levels."""

from pathlib import Path
from typing import (TYPE_CHECKING, Any, Callable, Dict, Generator, List,
                    Optional, cast)

from attr import Factory, attrib, attrs

from .action_map import ActionMap
from .pyglet import schedule_once
from .sound import AlreadyDestroyed, Sound, SoundManager
from .types import EventType

try:
    from synthizer import Context
except ModuleNotFoundError:
    Context = object

from .ambiance import Ambiance
from .mixins import RegisterEventMixin
from .track import Track, TrackTypes

if TYPE_CHECKING:
    from .game import Game
    from .types import MotionFunctionType, MotionsType


@attrs(auto_attribs=True)
class Level(RegisterEventMixin, ActionMap):
    """A level in a :class:`~earwax.Game` instance.

    An object that contains event handlers. Can be pushed and pulled from
    within a :class:`~earwax.Game` instance.

    While the :class:`~earwax.Game` object is the centre of a game, `Level`
    instances are where the magic happens.

    If the included :meth:`~earwax.Level.action` and
    :meth:`~earwax.Level.motion` decorators aren't enough for your needs, and
    you want to harness the full power of the Pyglet event system, simply
    subclass :class:`earwax.Level`, and include the requisite events. The
    underlying :class:`~earwax.Game` object will do all the heavy lifting for
    you, by way of the :class:`~earwax.EventMatcher` framework.

    :ivar ~earwax.Level.game: The game this level is bound to.

    :ivar ~earwax.Level.actions: A list of actions which can be called on this
        object. To define more, use the :meth:`~earwax.Level.action` decorator.

    :ivar ~earwax.Level.motions: The defined motion events. To define more, use
        the :meth:`~earwax.Level.motion` decorator.

    :ivar ~earwax.BoxLevel.ambiances: The ambiances for this level.

    :ivar ~earwax.BoxLevel.tracks: The tracks (musical or otherwise) that play
        while this level is top of the stack.
    """

    game: 'Game'

    motions: 'MotionsType' = attrib(Factory(dict), init=False, repr=False)

    ambiances: List['Ambiance'] = attrib(
        default=Factory(list), init=False, repr=False
    )
    tracks: List[Track] = attrib(default=Factory(list), init=False, repr=False)

    def __attrs_post_init__(self) -> None:
        """Register default events."""
        for func in (
            self.on_pop, self.on_push, self.on_reveal, self.on_text_motion,
            self.on_cover
        ):
            self.register_event(cast(EventType, func))

    def start_ambiances(self) -> None:
        """Start all the ambiances on this instance."""
        if self.game.ambiance_sound_manager is None:
            raise RuntimeError(
                'Unable to start ambiances with no ambiance sound manager.'
            )
        ambiance: Ambiance
        for ambiance in self.ambiances:
            ambiance.play(self.game.ambiance_sound_manager)

    def stop_ambiances(self) -> None:
        """Stop all the ambiances on this instance."""
        ambiance: Ambiance
        for ambiance in self.ambiances:
            ambiance.stop()

    def start_tracks(self) -> None:
        """Start all the tracks on this instance."""
        manager: Optional[SoundManager]
        track: Track
        for track in self.tracks:
            if track.track_type is TrackTypes.ambiance:
                manager = self.game.ambiance_sound_manager
            elif track.track_type is TrackTypes.music:
                manager = self.game.music_sound_manager
            else:
                raise RuntimeError(
                    'Unknown track type: %r.' % track.track_type
                )
            if manager is None:
                raise RuntimeError(
                    f'Unable to play {track!r} with no sound manager.'
                )
            track.play(manager)

    def stop_tracks(self) -> None:
        """Stop all the tracks on this instance."""
        track: Track
        for track in self.tracks:
            track.stop()

    def on_text_motion(self, motion: int) -> None:
        """Call the appropriate motion.

        The :attr:`~earwax.Level.motions` dictionary will be consulted, and if
        the provided motion is found, then that function will be called.

        This is the default event that is used by ``pyglet.window.Window``.

        :param motion: One of the motion constants from `pyglet.window.key
            <https://pythonhosted.org/pyglet/api/pyglet.window.key-
            module.html>`__.
        """
        if motion in self.motions:
            self.motions[motion]()

    def motion(self, motion: int) -> Callable[
        ['MotionFunctionType'], 'MotionFunctionType'
    ]:
        """Add a handler to :attr:`~earwax.Level.motions`.

        For example::

            @level.motion(key.MOTION_LEFT)
            def move_left():
                # ...

        This is the method used by :class:`earwax.Editor`, to make text
        editable, and :class:`earwax.Menu`, to make menus searchable.

        :param motion: One of the motion constants from `pyglet.window.key
            <https://pythonhosted.org/pyglet/api/pyglet.window.key-
            module.html>`__.
        """

        def inner(func: 'MotionFunctionType') -> 'MotionFunctionType':
            self.motions[motion] = func
            return func

        return inner

    def on_push(self) -> None:
        """Run code when this level is pushed.

        This event is called when a level has been pushed onto the :attr:`level
        stack <earwax.Game.levels>` of a game.
        """
        self.start_ambiances()
        self.start_tracks()

    def on_pop(self) -> None:
        """Run code when this level is popped.

        This event is called when a level has been popped from the :attr:`level
        stack <earwax.Game.levels>` of a game.
        """
        self.stop_ambiances()
        self.stop_tracks()

    def on_cover(self, level: 'Level') -> None:
        """Code to run when this level has been covered by a new one."""
        pass

    def on_reveal(self) -> None:
        """Code to be run when this level is exposed.

        This event is called when the level above this one in the stack has
        been popped, thus revealing this level.
        """
        pass


@attrs(auto_attribs=True)
class IntroLevel(Level):
    """An introduction level.

    This class represents a level that plays some audio, before optionally
    replacing itself in the level stack with :attr:`self.level
    <earwax.IntroLevel.level>`.

    If you want it to be possible to skip this level, add a trigger for the
    :meth:`~earwax.IntroLevel.skip` action.

    :ivar ~earwax.IntroLevel.level: The level that will replace this one.

    :ivar ~earwax.IntroLevel.sound_path: The sound to play when this level is
        pushed.

    :ivar ~earwax.IntroLevel.skip_after: An optional number of seconds to wait
        before skipping this level.

        If this value is ``None``, then the level will not automatically skip
        itself, and you will have to provide some other means of getting past
        it.

    :ivar ~earwax.IntroLevel.looping: Whether or not the playing sound should
        loop.

        If this value is ``True``, then :attr:`~earwax.IntroLevel.skip_after`
        must be ``None``, otherwise ``AssertionError`` will be raised.

    :ivar ~earwax.IntroLevel.sound_manager: The sound manager to use to play
        the sound.

        If this value is ``None``, then the sound will not be playing.

        This value default to :attr:`earwax.Game.interface_sound_manager`.

    :ivar ~earwax.IntroLevel.play_kwargs: Extra arguments to pass to the
        :meth:`~earwax.SoundManager.play` method of the
        :attr:`~earwax.IntroLevel.sound_manager`.

        When the :meth:`~earwax.IntroLevel.on_push` event is dispatched, an
        error will be raised if this dictionary contains a ``looping`` key, as
        2 ``looping`` arguments would be passed to
        :meth:`self.sound_manager.play_path <earwax.SoundManager.play_path>`.

    :ivar ~earwax.IntroLevel.sound: The sound object which represents the
        playing sound.

        If this value is ``None``, then the sound will not be playing.
    """

    level: Level
    sound_path: Path
    skip_after: Optional[float] = None
    looping: bool = False

    sound_manager: Optional[SoundManager] = attrib(repr=False)

    @sound_manager.default
    def get_default_sound_manager(
        instance: 'IntroLevel'
    ) -> Optional[SoundManager]:
        """Return a suitable sound manager."""
        return instance.game.interface_sound_manager

    play_kwargs: Dict[str, Any] = Factory(dict)

    sound: Optional[Sound] = attrib(
        default=Factory(type(None)), init=False, repr=False
    )

    def __attrs_post_init__(self) -> None:
        """Run sanity checks on the setup of this instance."""
        assert self.looping is False or self.skip_after is None
        super().__attrs_post_init__()

    def on_push(self) -> None:
        """Run code when this level has been pushed.

        Starts playing :attr:`self.sound_path <earwax.IntroLevel.sound_path>`,
        and optionally schedules an automatic skip.
        """
        super().on_push()
        if self.sound_manager is None:
            raise RuntimeError(
                'Cannot start playing without a valid sound manager.'
            )
        self.sound = self.sound_manager.play_path(
            self.sound_path, looping=self.looping, **self.play_kwargs
        )
        if self.skip_after is not None:
            schedule_once(
                lambda dt: self.game.replace_level(self.level)
                if self.game.level is self else None,
                self.skip_after
            )

    def on_pop(self) -> None:
        """Destroy any created :meth:`~earwax.IntroLevel.sound`."""
        super().on_pop()
        if self.sound is not None:
            try:
                self.sound.destroy()
            except AlreadyDestroyed:
                pass
            finally:
                self.sound = None

    def skip(self) -> Generator[None, None, None]:
        """Skip this level.

        Replaces this level in the level stack with :attr:`self.level
        <earwax.IntroLevel.level>`.
        """
        if self.game.level is self:
            yield
            self.game.replace_level(self.level)
