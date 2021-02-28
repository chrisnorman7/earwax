"""Provides the Die class."""

from random import randint

from attr import attrs

from .mixins import RegisterEventMixin


@attrs(auto_attribs=True)
class Die(RegisterEventMixin):
    """A single dice.

    :ivar ~earwax.Die.sides: The number of sides this die has.
    """

    sides: int = 6

    def __attrs_post_init__(self) -> None:
        """Register default events."""
        self.register_event(self.on_roll)

    def on_roll(self, value: int) -> None:
        """Code to be run when a die is rolled.

        An event which is dispatched by :meth:`~earwax.Die.roll` method.

        :param value: The number that has been rolled.
        """
        pass

    def roll(self) -> int:
        """Roll a die.

        Returns a number between 1, and :attr:`self.size
        <earwax.Die.size>`.
        """
        value: int = randint(1, self.sides)
        self.dispatch_event("on_roll", value)
        return value
