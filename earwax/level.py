"""Provides classes for working with levels."""

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Generator, List, Optional

from attr import Factory, attrib, attrs

try:
    from pyglet.clock import schedule_once
except ModuleNotFoundError:
    pass
if TYPE_CHECKING:
    from synthizer import Buffer, BufferGenerator, Context, DirectSource

from .action import Action, ActionFunctionType
from .ambiance import Ambiance
from .mixins import RegisterEventMixin
from .sound import get_buffer
from .track import Track

if TYPE_CHECKING:
    from .game import Game
    from .types import ActionListType, MotionFunctionType, MotionsType


@attrs(auto_attribs=True)
class Level(RegisterEventMixin):
    """An object that contains event handlers. Can be pushed and pulled from
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

    actions: 'ActionListType' = attrib(default=Factory(list), init=False)
    motions: 'MotionsType' = attrib(Factory(dict), init=False)

    ambiances: List['Ambiance'] = attrib(default=Factory(list), init=False)
    tracks: List[Track] = attrib(default=Factory(list), init=False)

    def __attrs_post_init__(self) -> None:
        for func in (
            self.on_pop, self.on_push, self.on_reveal, self.on_text_motion,
            self.on_cover
        ):
            self.register_event_type(func.__name__)

    def start_ambiances(self) -> None:
        """Start all the ambiances on this instance."""
        ctx: Optional[Context] = self.game.audio_context
        if ctx is None:
            raise RuntimeError('Cannot start ambiances with no audio context.')
        ambiance: Ambiance
        for ambiance in self.ambiances:
            ambiance.play(ctx)

    def stop_ambiances(self) -> None:
        """Stops all the ambiances on this instance."""
        ambiance: Ambiance
        for ambiance in self.ambiances:
            ambiance.stop()

    def start_tracks(self) -> None:
        """Start all the tracks on this instance."""
        ctx: Optional[Context] = self.game.audio_context
        if ctx is None:
            raise RuntimeError('Cannot start tracks with no audio context.')
        track: Track
        if self.game.audio_context is not None:
            for track in self.tracks:
                track.play(ctx)

    def stop_tracks(self) -> None:
        """Stop all the tracks in :attr:`self.tracks
        <earwax.BoxLevel.tracks>`."""
        track: Track
        if self.game.audio_context is not None:
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

    def action(self, name: str, **kwargs) -> Callable[
        [ActionFunctionType], Action
    ]:
        """A decorator to add an action to this level::

            @level.action(
                'Walk forwards', symbol=key.W, mouse_button=mouse.RIGHT,
                interval=0.5
            )
            def walk_forwards():
                # ...

        :param name: The name of the new action.

            The name is currently only used by :class:`earwax.ActionMenu`.

        :param kwargs: Extra keyword arguments to passed along to the
            constructor of :class:`earwax.Action`.
        """

        def inner(func: ActionFunctionType) -> Action:
            """Actually add the action."""
            a: Action = Action(self, name, func, **kwargs)
            self.actions.append(a)
            return a

        return inner

    def motion(self, motion: int) -> Callable[
        ['MotionFunctionType'], 'MotionFunctionType'
    ]:
        """A decorator to add a handler to self.motions::

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
        """The event which is called when a level has been pushed onto the
        level stack of a game."""
        self.start_ambiances()
        self.start_tracks()

    def on_pop(self) -> None:
        """The event which is called when a level has been popped from thelevel
        stack of a game."""
        self.stop_ambiances()
        self.stop_tracks()

    def on_cover(self, level: 'Level') -> None:
        """This level has just been covered by a new one."""
        pass

    def on_reveal(self) -> None:
        """The event which is called when the level above this one in the stack
        has been popped, thus revealing this level."""
        pass


@attrs(auto_attribs=True)
class IntroLevel(Level):
    """A level that plays some audio, before optionally replacing itself in the
    level stack with :attr:`self.level <earwax.IntroLevel.level>`.

    If you want it to be possible to skip this level, add a trigger for the
    :meth:`~earwax.IntroLevel.skip` action.

    :ivar ~earwax.IntroLevel.level: The level that will replace this one.

    :ivar ~earwax.IntroLevel.sound_path: The sound to play when this level is
        pushed.

    :ivar ~earwax.IntroLevel.skip_after: An optional number of seconds to add
        to the length of the sound buffer before skipping this level.

        If this value is ``None``, then the level will not automatically skip
        itself, and you will have to provide some other means of skipping.

    :ivar ~earwax.IntroLevel.looping: Whether or not :attr:`self.generator
        <earwax.IntroLevel.generator>` should loop.

        If this value is ``True``, then :attr:`self.skip_after
        <earwax.IntroLevel.skip_after>` must be ``None``, otherwise
        ``AssertionError`` will be raised.

    :ivar ~earwax.IntroLevel.generator: The ``synthizer.BufferGenerator`` to
        play the sound through.

    :ivar ~earwax.IntroLevel.source: The source to play :attr:`self.generator
        <earwax.IntroLevel.buffer>` through.
    """

    level: Level
    sound_path: Path
    skip_after: Optional[float]
    looping: bool = False

    generator: Optional['BufferGenerator'] = None
    source: Optional['DirectSource'] = None

    def __attrs_post_init__(self) -> None:
        assert self.looping is False or self.skip_after is None
        super().__attrs_post_init__()

    def on_push(self) -> None:
        """Start playing :attr:`self.sound_path
        <earwax.IntroLevel.sound_path>`, and optionally schedule an automatic
        skip.
        """
        super().on_push()
        ctx: Optional[Context] = self.game.audio_context
        if ctx is None:
            raise RuntimeError(
                'Cannot start playing without a valid audio context.'
            )
        self.source = DirectSource(ctx)
        self.generator = BufferGenerator(ctx)
        self.source.add_generator(self.generator)
        self.generator.looping = self.looping
        buffer: Buffer = get_buffer('file', str(self.sound_path))
        self.generator.buffer = buffer
        if self.skip_after is not None:
            schedule_once(
                lambda dt: self.skip(),
                self.skip_after + buffer.get_length_in_seconds()
            )

    def on_pop(self) -> None:
        """Destroy :attr:`self.generator <earwax.IntroLevel.generator>`, and
        :attr:`self.source <earwax.IntroLevel.source>`.
        """
        super().on_pop()
        if self.generator is not None:
            self.generator.destroy()
            self.generator = None
        if self.source is not None:
            self.source.destroy()
            self.source = None

    def skip(self) -> Generator[None, None, None]:
        """Replace this level in the level stack with :attr:`self.level
        <earwax.IntroLevel.level>`."""
        if self.game.level is self:
            yield
            self.game.replace_level(self.level)
