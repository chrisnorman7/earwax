"""Provides the Die class."""

from random import randint

from attr import attrs

try:
    from pyglet.event import EventDispatcher
except ModuleNotFoundError:
    EventDispatcher = object


@attrs(auto_attribs=True)
class Die(EventDispatcher):
    """A single dice.

    :ivar ~earwax.Die.sides: The number of sides this die has.
    """

    sides: int = 6

    def __attrs_post_init__(self) -> None:
        self.register_event_type('on_roll')

    def on_roll(self, value: int) -> None:
        """An event which is dispatched by :meth:`~earwax.Die.roll` method.

        :param value: The number that has been rolled.
        """
        pass

    def roll(self) -> int:
        """Returns a number between 1, and :attr:`self.size
        <earwax.Die.size>`.
        """
        value: int = randint(1, self.sides)
        self.dispatch_event('on_roll', value)
        return value
