"""Provides the Action class."""

from time import time
from typing import TYPE_CHECKING, Callable, Generator, Optional, Tuple

from attr import Factory, attrib, attrs

if TYPE_CHECKING:
    from .level import Level

OptionalGenerator = Optional[Generator[None, None, None]]
ActionFunctionType = Callable[[], OptionalGenerator]
HatDirection = Tuple[int, int]


@attrs(auto_attribs=True)
class Action:
    """An action that can be called from within a game.

    Actions are added to :class:`~earwax.Level` instances.

    Usually, this class is not used directly, but returned by the
    :meth:`earwax.Level.action` method.

    :ivar ~earwax.Action.level: The level this action is bound to.

    :ivar ~earwax.Action.title: The title of this action.

    :ivar ~earwax.Action.func: The function to run.

    :ivar ~earwax.Action.symbol: The keyboard symbol to be used (should be one
        of the symbols from `pyglet.window.key
        <https://pyglet.readthedocs.io/en/latest/programming_guide/
        keyboard.html>`_).

    :ivar ~earwax.Action.mouse_button: The mouse button to be used (should be
        one of the symbols from `pyglet.window.mouse
        <https://pyglet.readthedocs.io/en/latest/programming_guide/
        mouse.html>`_).

    :ivar ~earwax.Action.modifiers: Keyboard modifiers. Should be made up of
        modifiers from pyglet.window.key.

    :ivar ~earwax.Action.joystick_button: The button that must be pressed on a
        game controler to trigger this action.

        The button can be any integer supported by any game pad.

    :ivar ~earwax.Action.hat_direction: The position the hat must be in to
        trigger this action.

        This value must be one of the members of :var:`earwax.HatPositions`.

    :ivar ~earwax.Action.interval: How often this action can run.

        If ``None``, then it is a one-time action. One-time actions should be
        used for things like quitting the game, or passing through exits, where
        multiple uses in a short space of time would be undesireable. If the
        value is an integer, it will be the number of seconds which must elapse
        between runs.

    :ivar ~earwax.Action.last_run: The time this action was last run.

        To get the number of seconds since an action was last run, use ``time()
        - action.last_run``.
    """

    level: 'Level'
    title: str
    func: ActionFunctionType
    symbol: Optional[int] = None
    mouse_button: Optional[int] = None
    modifiers: int = 0
    joystick_button: Optional[int] = None
    hat_direction: Optional[HatDirection] = None
    interval: Optional[int] = Factory(lambda: None)
    last_run: float = attrib(default=Factory(float), init=False)

    def run(self, dt: Optional[float]) -> OptionalGenerator:
        """Run this action. May be called by
        ``pyglet.clock.schedule_interval``.

        If you need to know how an action has been called, you can override
        this method and check ``dt``.

        It will be ``None`` if it wasn't called by ``schedule_interval``. This
        will happen either if you are dealing with a one-time action
        (:attr:`~earwax.Action.interval` is ``None``), or the action is being
        called as soon as it is triggered (``schedule_interval`` doesn't allow
        a function to be run and scheduled in one call).

        If you need to call an action from your own code, you should use::

            action.run(None)

        :param dt: Refer to the documentation for `pyglet.clock
            <https://pyglet.readthedocs.io/en/latest/modules/clock.html>`_.
        """
        now: float = time()
        if self.interval is not None:
            if dt is None:
                dt = now - self.last_run
            if dt < self.interval:
                return None
        self.last_run = now
        return self.func()

    def __str__(self) -> str:
        """Return a string representing this action."""
        return self.title
