"""Provides classes for working with levels."""

from typing import TYPE_CHECKING, Callable

from attr import Factory, attrib, attrs

from .action import Action, ActionFunctionType

if TYPE_CHECKING:
    from .game import Game, ActionListType, MotionsType, MotionFunctionType

from .speech import tts


@attrs(auto_attribs=True)
class Level:
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

    :ivar ~earwax.Level.actions: A list of actions which can be called on this
        object. To define more, use the :meth:`~earwax.Level.action` decorator.

    :ivar ~earwax.Level.motions: The defined motion events. To define more, use
        the :meth:`~earwax.Level.motion` decorator.
    """

    actions: 'ActionListType' = attrib(default=Factory(list), init=False)
    motions: 'MotionsType' = attrib(Factory(dict), init=False)

    def on_text_motion(self, motion: int) -> None:
        """Call the appropriate motion.

        The :attr:`~earwax.Level.motions` dictionary will be consulted, and if
        the provided motion is found, then that function will be called.

        This is the default event that is used by `pyglet.window.Window`.
        """
        if motion in self.motions:
            self.motions[motion]()

    def action(self, name: str, **kwargs) -> Callable[
        [ActionFunctionType], Action
    ]:
        """A decorator to add an action to this level.

        >>> @level.action(
        ...     'Walk forwards', symbol=key.W, mouse_button=mouse.RIGHT,
        ...     interval=0.5
        ... )
        ... def walk_forwards():
        ...     # ...

        All extra keyword arguments are passed along to the constructor of
        :class:`earwax.Action`.
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
        """A decorator to add a handler to self.motions.

        >>> @level.motion(key.MOTION_LEFT)
        >>>def move_left():
        ...     # ...
        """

        def inner(func: 'MotionFunctionType') -> 'MotionFunctionType':
            self.motions[motion] = func
            return func

        return inner

    def on_push(self) -> None:
        """The event which is called when a level has been pushed onto the
        level stack of a game."""
        pass

    def on_pop(self) -> None:
        """The event which is called when a level has been popped from thelevel
        stack of a game."""
        pass

    def on_reveal(self) -> None:
        """The event which is called when the level above this one in the stack
        has been popped, thus revealing this level."""
        pass


@attrs(auto_attribs=True)
class GameMixin:
    """Add a game attribute to any :class:`Level` subclass.

    :ivar ~earwax.level.GameMixin.game: The game this level is bound to.
    """

    game: 'Game'


@attrs(auto_attribs=True)
class DismissibleMixin(GameMixin):
    """Make any :class:`Level` subclass dismissible.

    :ivar ~earwax.level.DismissibleMixin.dismissible: Whether or not it should
        be possible to dismiss this level.
    """

    dismissible: bool = Factory(lambda: True)

    def dismiss(self) -> None:
        """Dismiss the currently active level.

     By default, when used by :class:`earwax.Menu` and :class:`earwax.Editor`,
     this method is called when the escape key is pressed, and only if
     :attr:`self.dismissible <earwax.level.DismissibleMixin.dismissible>`
     evaluates to True.

     The default implementation simply calls :meth:`~earwax.Game.pop_level` on
     the attached :class:`earwax.Game` instance."""
        if self.dismissible:
            self.game.pop_level()
            tts.speak('Cancel.')


@attrs(auto_attribs=True)
class TitleMixin:
    """Add a title to any :class:`Level` subclass.

    :ivar ~earwax.level.TitleMixin.title: The title of this menu.
    """

    title: str
