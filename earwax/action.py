"""Provides the Action class."""

from time import time
from typing import TYPE_CHECKING, Callable, Generator, List, Optional

from attr import Factory, attrib, attrs
from pyglet.window import key

if TYPE_CHECKING:
    from .level import Level

OptionalGenerator = Optional[Generator[None, None, None]]
ActionFunctionType = Callable[[], OptionalGenerator]


@attrs(auto_attribs=True)
class Action:
    """An action that can be called from within a game."""

    # The level this action is bound to.
    level: 'Level'

    # The title of this action.
    title: str

    # The function to run.
    func: ActionFunctionType

    # The keyboard symbol to be used (should be one of the symbols from
    # pyglet.window.key).
    symbol: Optional[int] = None

    # Keyboard modifiers. Should be made up of modifiers from
    # pyglet.window.key.
    modifiers: int = 0

    # How often this action can run.
    #
    # If None, then it is a one-time action. This type of action should be used
    # for things like quitting the game, or passing through an exit, where
    # multiple uses in a short space of time would be undesireable.
    # Otherwise, this will be the number of seconds which must elapse between
    # runs.
    interval: Optional[int] = Factory(lambda: None)

    # The time this action was last run.
    last_run: float = attrib(default=Factory(float), init=False)

    def run(self, dt: Optional[float]) -> OptionalGenerator:
        """Run this action. May be called by
        pyglet.clock.schedule_interval.

        If you need to know how this action has been called, you can check dt.
        It will be None if it wasn't called by schedule_interval.

        This will happen either if this is a one-time action (interval is
        None), or it is being called as soon as it is triggered
        (schedule_interval doesn't allow a function to be run and
        scheduled in one call)."""
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
        s: str = self.title
        triggers: List[str] = []
        if self.symbol:
            key_string: str = key.symbol_string(self.symbol)
            if self.modifiers:
                modifiers_string: str = key.modifiers_string(self.modifiers)
                modifiers_string = modifiers_string.replace('|', '+')\
                    .replace('MOD_', '')
                key_string = f'{modifiers_string} + {key_string}'
            triggers.append(key_string)
        if triggers:
            s += f' [{" | ".join(triggers)}]'
        return s
