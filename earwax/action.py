"""Provides the Action class."""

from time import time
from typing import Optional

from attr import Factory, attrib, attrs

from .types import ActionFunctionType, HatDirection, OptionalGenerator


@attrs(auto_attribs=True)
class Action:
    """An action that can be called from within a game.

    Actions can be added to :class:`~earwax.Level`, and
    :class:`~earwax.ActionMap` instances.

    Usually, this class is not used directly, but returned by the
    :meth:`~earwax.ActionMap.action` method of whatever :class:`~earwax.Level`
    or :class:`~earwax.ActionMap` instance it is bound to.

    :ivar ~earwax.Action.title: The title of this action.

    :ivar ~earwax.Action.func: The function to run.

        If this value is a normal function, it will be called when the action
        is triggered.

        If this function is a generator, any code before the first ``yield``
        statement will be run when the triggering key, hat, joystick button, or
        mouse button is pressed down. Anything after that will be run when the
        same trigger is released.

        It is worth noting that the behaviour of having a generator that yields
        more than once is undefined.

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
        game controller to trigger this action.

        The button can be any integer supported by any game pad.

    :ivar ~earwax.Action.hat_direction: The position the hat must be in to
        trigger this action.

        This value must be a value supported by the hat control on the
        controller you're targetting.

        There are some helpful default values in :mod:`earwax.hat_directions`.
        If they do not suit your purposes, simply provide your own tuple.

        It is worth noting that if you rely on the hat, there are a few things
        to be aware of:

        If you rely on generators in hat-triggered actions, then all actions
        that have yielded will be stopped when the hat returns to its default
        position. This is because Earwax does not attempt to keep track of the
        last direction, and the hat does not generate release events like
        joystick buttons do.

    :ivar ~earwax.Action.interval: How often this action can run.

        If ``None``, then it is a one-time action. One-time actions should be
        used for things like quitting the game, or passing through exits, where
        multiple uses in a short space of time would be undesirable. Otherwise,
        it will be the number of seconds which must elapse between runs.

    :ivar ~earwax.Action.last_run: The time this action was last run.

        To get the number of seconds since an action was last run, use ``time()
        - action.last_run``.
    """

    title: str
    func: ActionFunctionType
    symbol: Optional[int] = None
    mouse_button: Optional[int] = None
    modifiers: int = 0
    joystick_button: Optional[int] = None
    hat_direction: Optional[HatDirection] = None
    interval: Optional[float] = None
    last_run: float = attrib(default=Factory(float), init=False)

    def run(self, dt: Optional[float]) -> OptionalGenerator:
        """Run this action.

        This method may be called by
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
