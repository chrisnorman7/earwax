"""Provides the Action class."""

from time import time

from attr import Factory, attrib, attrs

NoneType = type(None)


@attrs
class Action:
    """An action that can be called from within a game."""

    # The title of this action.
    title = attrib()

    # The function to run.
    func = attrib()

    # The keyboard symbol to be used (should be one of the symbols from
    # pyglet.window.key).
    symbol = attrib(default=Factory(NoneType))

    # Keyboard modifiers. Should be made up of modifiers from
    # pyglet.window.key.
    modifiers = attrib(default=Factory(int))

    # How often this action can run.
    #
    # If None, then it is a one-time action. This type of action should be used
    # for things like quitting the game, or passing through an exit, where
    # multiple uses in a short space of time would be undesireable.
    # Otherwise, this will be the number of seconds which must elapse between
    # runs.
    interval = attrib(default=Factory(NoneType))

    # The time this action was last run.
    last_run = attrib(default=Factory(float))

    # The game this action is bound to.
    game = attrib(default=Factory(NoneType))

    def run(self, dt):
        """Run this action. Will be called by
        pyglet.clock.schedule_interval."""
        now = time()
        if dt is None:
            dt = now - self.last_run
        if dt >= self.interval:
            self.last_run = now
            self.func()
