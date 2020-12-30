"""Provides various mixin classes for used with other objects."""

from typing import TYPE_CHECKING, Tuple

from attr import attrs

try:
    from pyglet.event import EventDispatcher
except ModuleNotFoundError:
    EventDispatcher = object

if TYPE_CHECKING:
    from .game import Game
    from .types import EventType


@attrs(auto_attribs=True)
class DismissibleMixin:
    """Make any :class:`Level` subclass dismissible.

    :ivar ~earwax.mixins.DismissibleMixin.dismissible: Whether or not it should
        be possible to dismiss this level.
    """

    dismissible: bool = True

    def dismiss(self) -> None:
        """Dismiss the currently active level.

        By default, when used by :class:`earwax.Menu` and
        :class:`earwax.Editor`, this method is called when the escape key is
        pressed, and only if :attr:`self.dismissible
        <earwax.level.DismissibleMixin.dismissible>` evaluates to ``True``.

        The default implementation simply calls :meth:`~earwax.Game.pop_level`
        on the attached :class:`earwax.Game` instance, and announces the
        cancellation.
        """
        if self.dismissible:
            self.game: 'Game'
            self.game.pop_level()
            self.game.output('Cancel.')


@attrs(auto_attribs=True)
class TitleMixin:
    """Add a title to any :class:`Level` subclass.

    :ivar ~earwax.level.TitleMixin.title: The title of this instance.
    """

    title: str


@attrs(auto_attribs=True)
class CoordinatesMixin:
    """Add 3d coordinates to any object."""

    x: float
    y: float
    z: float

    @property
    def coordinates(self) -> Tuple[float, float, float]:
        """Return ``self.x``, ``self.y``, and ``self.z`` as a tuple."""
        return self.x, self.y, self.z


class RegisterEventMixin(EventDispatcher):
    """Allow registering and binding events in one function."""

    def register_event(self, func: 'EventType') -> str:
        """Register an event type from a function.

        This function uses ``func.__name__`` to register an event type,
        eliminating possible typos in event names.

        :param func: The function whose name will be used.
        """
        return self.register_event_type(func.__name__)

    def register_and_bind(self, func: 'EventType') -> 'EventType':
        """Register and bind a new event.

        This is the same as::

            level.register_event_type('f')

            @level.event
            def f() -> None:
                pass

        :param func: The function whose name will be registered, and which will
            be bound to this instance.
        """
        self.register_event(func)
        return self.event(func)
