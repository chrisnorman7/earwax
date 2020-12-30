"""Provides the EventMatcher class."""

from typing import TYPE_CHECKING

from attr import attrs

if TYPE_CHECKING:
    from .game import Game


@attrs(auto_attribs=True)
class EventMatcher:
    """Matches events for :class:`~earwax.Game` instances.

    An object to call events on a :class:`~earwax.Game` instance's
    :attr:`~earwax.Game.level` property.

    Used to prevent us writing loads of events out.

    :ivar ~earwax.EventMatcher.game: The game this matcher is bound to.

    :ivar ~earwax.EventMatcher.name: The name of the event this matcher uses.
    """

    game: 'Game'
    name: str

    def dispatch(self, *args, **kwargs) -> None:
        """Dispatch this event.

        Find the appropriate event on game.level, if game.level is not
        None.

        If :attr:`self.game.level <earwax.Game.level>` doesn't have an event of
        the proper name, search instead on :attr:`self.game
        <earwax.EventMatcher.game>`.

        :param args: The positional arguments to pass to any event that is
            found.

        :param kwargs: The keyword arguments to pass to any event that is
            found.
        """
        if (
            self.game.level is not None and
            self.name in self.game.level.event_types
        ):
            return self.game.level.dispatch_event(self.name, *args, **kwargs)
        if self.name in self.game.event_types:
            return self.game.dispatch_event(self.name, *args, **kwargs)
