"""Provides the Game class."""


from typing import List, Optional

from attr import Factory, attrib, attrs
from pyglet import app, options
from pyglet.window import Window
from synthizer import initialized

from .level import Level


@attrs(auto_attribs=True)
class Game:
    """The main game object.

    This object holds a reference to the game window, as well as a list of
    Level instances.

    Instances of the Level class can be pushed, popped, and replaced. The
    entire stack can also be cleared.

    Each Level instance should be prepared to handle all window events."""

    # The window to display the game.
    window: Optional[Window] = attrib(
        default=Factory(lambda: None), init=False
    )

    # All the pushed levels.
    levels: List[Level] = attrib(default=Factory(list), init=False)

    def before_run(self) -> None:
        """This hook is called by the run method, just before pyglet.app.run is
        called.

        By this point, default events have been decorated, such as
        on_key_press, and on_text. Also, we are inside a synthizer.initialized
        context manager, so feel free to play sounds."""
        pass

    def run(self, window: Window) -> None:
        """Run the game."""
        options['shadow_window'] = False
        self.window = window
        self.window.event(self.on_key_press)
        self.window.event(self.on_key_release)
        self.window.event(self.on_text)
        self.window.event(self.on_text_motion)
        with initialized():
            self.before_run()
            app.run()

    def push_level(self, level: Level) -> None:
        """Push a level onto self.levels."""
        self.levels.append(level)
        level.on_push()

    def replace_level(self, level: Level) -> None:
        """Pop the current level, then push the new one."""
        self.pop_level()
        self.push_level(level)

    def pop_level(self) -> None:
        """Pop the most recent level from the stack."""
        level: Level = self.levels.pop()
        level.on_pop()
        if self.levels:
            self.levels[-1].on_reveal()

    def clear_levels(self) -> None:
        """Pop all levels."""
        while self.levels:
            self.pop_level()

    @property
    def level(self) -> Optional[Level]:
        """Get the most recently added menu."""
        if len(self.levels):
            return self.levels[-1]
        return None

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """If we have a level, call its on_key_press method. Otherwise, do
        nothing."""
        if self.level is not None:
            return self.level.on_key_press(symbol, modifiers)
        return False

    def on_key_release(self, symbol: int, modifiers: int) -> bool:
        """If we have a level, call its on_key_release method. Otherwise, do
        nothing."""
        if self.level is not None:
            return self.level.on_key_release(symbol, modifiers)
        return False

    def on_text(self, text: str) -> bool:
        """If we have a level, call its on_text method. Otherwise, do
        nothing."""
        if self.level is not None:
            return self.level.on_text(text)
        return False

    def on_text_motion(self, motion: int) -> bool:
        """If we have a level, call its on_text_motion method. Otherwise, do
        nothing."""
        if self.level is not None:
            return self.level.on_text_motion(motion)
        return False
