"""Provides the RumbleEffect class."""

from math import floor
from typing import TYPE_CHECKING, Generator

from attr import attrs
from pyglet.input import Joystick

from .promises.staggered_promise import StaggeredPromise

if TYPE_CHECKING:
    from .game import Game


@attrs(auto_attribs=True)
class RumbleEffect:
    """A rumble effect.

    Instances of this class create rumble "waves", with a start, a climb in
    effect to an eventual peak, then, after some time at the peak, a gradual
    drop back to stillness.

    For example, you could have an effect that started at 0.5 (half power),
    then climbed in increments of 0.1 every 10th of a second to a peak value of
    1.0 (full power), then stayed there for 1 second, before reducing back down
    to 0.7 (70% power), with 0.1 decrements every 0.2 seconds.

    The code for this effect would be::

        effect: RumbleEffect = RumbleEffect(
            0.5,  # start_value
            0.1,  # increase_interval
            0.1,  # increase_value
            1.,  # peak_duration
            1.0,  # peak_value
            0.2,  # decrease_interval
            0.1,  # decrease_value
            0.7,  # end_value
        )

    The :meth:`~earwax.RumbleEffect.start` method returns an instance of
    :class:`~earwax.StaggeredPromise`. This gives you the ability to save your
    effect, then use it at will::

        effect: RumbleEffect = RumbleEffect(
            0.2,  # start_value
            0.3,  # increase_interval
            0.1,  # increase_value
            1.5,  # peak_duration
            1.0,  # peak_value
            0.3,  # decrease_interval
            0.1,  # decrease_value
            0.1,  # end_value
        )
        # ...
        promise: StaggeredPromise = effect.start(game, 0)
        promise.run()

    *Please note*:

    When we talk about a rumble *value*, we mean a value from ``0.0``
    (nothing), to ``1.0`` (full on).

    In reality, values on the lower end can barely be felt with some
    controllers.

    :ivar ~earwax.RumbleEffect.start_value: The initial rumble value.

    :ivar ~earwax.RumbleEffect.increase_interval: How many seconds should
        elapse between each increase.

    :ivar ~earwax.RumbleEffect.increase_value: How much should be added to the
        rumble value each increase.

    :ivar ~earwax.RumbleEffect.peak_duration: How many seconds the
        :attr:`~earwax.RumbleEffect.peak_value` rumble should be felt.

    :ivar ~earwax.RumbleEffect.peak_value: The highest rumble value this effect
        will achieve.

    :ivar ~earwax.RumbleEffect.decrease_interval: The number of seconds between
        decreases.

    :ivar ~earwax.RumbleEffect.decrease_value: How much should be subtracted
        from the rumble value each decrease.

    :ivar ~earwax.RumbleEffect.end_value: The last value that will be felt.
    """

    start_value: float
    increase_interval: float
    increase_value: float
    peak_duration: float
    peak_value: float
    decrease_interval: float
    decrease_value: float
    end_value: float

    def start(self, game: 'Game', joystick: Joystick) -> StaggeredPromise:
        """Start this effect.

        :param game: The game which will provide the
            :meth:`~earwax.Game.start_rumble`, and
            :meth:`~earwax.Game.stop_rumble` methods.

        :param joystick: The joystick to rumble.
        """

        @StaggeredPromise.decorate
        def inner() -> Generator[float, None, None]:
            """Run this effect."""
            value: float = self.start_value
            game.start_rumble(joystick, value, 0)
            while value < self.peak_value:
                yield self.increase_interval
                value = min(self.peak_value, value + self.increase_value)
                game.start_rumble(joystick, value, 0)
            yield self.increase_interval
            game.start_rumble(joystick, self.peak_value, 0)
            yield self.peak_duration
            while value > self.end_value:
                value = max(self.end_value, value - self.decrease_value)
                game.start_rumble(joystick, value, 0)
                yield self.decrease_interval
            game.start_rumble(
                joystick, self.end_value, floor(self.decrease_interval * 1000)
            )

        return inner
