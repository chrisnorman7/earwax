"""Provides the EventMatcher class."""

from typing import TYPE_CHECKING

from attr import attrs

if TYPE_CHECKING:
    from .game import Game


@attrs(auto_attribs=True)
class EventMatcher:
    """Used to prevent us writing loads of events out."""

    # The game this matcher is bound to.
    game: 'Game'

    # The name of the event this matcher uses.
    name: str

    def dispatch(self, *args, **kwargs) -> None:
        """Find the appropriate event on game.level, if game.level is not
        None."""
        if self.game.level is not None:
            if hasattr(self.game.level, self.name):
                return getattr(self.game.level, self.name)(*args, **kwargs)
        if hasattr(self.game, self.name):
            return getattr(self.game, self.name)(*args, **kwargs)
