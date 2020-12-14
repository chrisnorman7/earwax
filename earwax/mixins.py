"""Provides various mixin classes for used with other objects."""

from typing import TYPE_CHECKING, Any, Callable, Tuple

from attr import attrs

try:
    from pyglet.event import EventDispatcher
except ModuleNotFoundError:
    EventDispatcher = object

if TYPE_CHECKING:
    from .game import Game

EventFunction = Callable[..., Any]


@attrs(auto_attribs=True)
class DismissibleMixin:
    """Make any :class:`Level` subclass dismissible.

    :ivar ~earwax.level.DismissibleMixin.dismissible: Whether or not it should
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

    def register_event(self, func: EventFunction) -> str:
        """Register an event type from a function.

        This function simply registers the given event from its ``__name__`
        attribute, eliminating possible typos in event names.

        :param func: The function whose name will be used.
        """
        return self.register_event_type(func.__name__)
