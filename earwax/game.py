"""Provides the Game class."""

from inspect import isgenerator
from typing import Callable, Dict, Generator, Iterator, List, Optional, cast

import pyglet
from attr import Factory, attrib, attrs
from pyglet import app, clock
from pyglet.window import Window
from synthizer import initialized

from .action import Action, OptionalGenerator
from .level import Level

ActionListType = List[Action]
ReleaseGeneratorListType = Dict[int, Generator[None, None, None]]
MotionFunctionType = Callable[[], None]
MotionsType = Dict[int, MotionFunctionType]


@attrs(auto_attribs=True)
class Game:
    """The main game object.

    This object holds a reference to the game window, as well as a list of
    Level instances.

    Instances of the Level class can be pushed, popped, and replaced. The
    entire stack can also be cleared."""

    # The window to display the game.
    window: Optional[Window] = attrib(
        default=Factory(lambda: None), init=False
    )

    # All the pushed levels.
    levels: List[Level] = attrib(default=Factory(list), init=False)

    # The currently triggered actions.
    triggered_actions: 'ActionListType' = attrib(
        default=Factory(list), init=False
    )

    # The actions which returned generators, and need to do something on key
    # release.
    key_release_generators: ReleaseGeneratorListType = attrib(
        default=Factory(dict), init=False
    )

    # The actions which returned generators, and need to do something on mouse
    # release.
    mouse_release_generators: ReleaseGeneratorListType = attrib(
        default=Factory(dict), init=False
    )

    def start_action(self, a: Action) -> OptionalGenerator:
        """Start an action. If the action has no interval, it will be ran
        straight away. Otherwise, it will be added to triggered_actions."""
        if a.interval is not None:
            self.triggered_actions.append(a)
            clock.schedule_interval(a.run, a.interval)
        return a.run(None)

    def stop_action(self, a: Action) -> None:
        """Unschedule an action, and remove it from triggered_actions."""
        self.triggered_actions.remove(a)
        clock.unschedule(a.run)

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """A key has been pressed down."""
        if self.level is not None:
            a: Action
            for a in self.level.actions:
                if a.symbol == symbol and a.modifiers == modifiers:
                    res: OptionalGenerator = self.start_action(a)
                    if isgenerator(res):
                        next(cast(Iterator[None], res))
                        self.key_release_generators[symbol] = cast(
                            Generator[None, None, None], res
                        )
            return True
        return False

    def on_key_release(self, symbol: int, modifiers: int) -> bool:
        """A key has been released."""
        a: Action
        for a in self.triggered_actions:
            if a.symbol == symbol:
                self.stop_action(a)
        if symbol in self.key_release_generators:
            generator: Generator[
                None, None, None
            ] = self.key_release_generators.pop(symbol)
            try:
                next(generator)
            except StopIteration:
                pass
        return True

    def press_key(
        self, symbol: int, modifiers: int, string: Optional[str] = None,
        motion: Optional[int] = None
    ) -> None:
        """A method for use in tests. First presses the given key combination,
        then releases it.

        If string and motion are not None, then on_text, and on_text_motion
        events will also be fired."""
        self.on_key_press(symbol, modifiers)
        if string is not None:
            getattr(self, 'on_text', lambda s: None)(string)
        if motion is not None:
            getattr(self, 'on_text_motion', lambda m: None)(motion)
        self.on_key_release(symbol, modifiers)

    def on_mouse_press(
        self, x: int, y: int, button: int, modifiers: int
    ) -> bool:
        """A mouse button has been pressed down."""
        if self.level is not None:
            a: Action
            for a in self.level.actions:
                if a.mouse_button == button and a.modifiers == modifiers:
                    res: OptionalGenerator = self.start_action(a)
                    if isgenerator(res):
                        next(cast(Iterator[None], res))
                        self.mouse_release_generators[button] = cast(
                            Generator[None, None, None], res
                        )
            return True
        return False

    def on_mouse_release(
        self, x: int, y: int, button: int, modifiers: int
    ) -> bool:
        """A mouse button has been released."""
        a: Action
        for a in self.triggered_actions:
            if a.mouse_button == button:
                self.stop_action(a)
        if button in self.mouse_release_generators:
            generator: Generator[
                None, None, None
            ] = self.key_release_generators.pop(button)
            try:
                next(generator)
            except StopIteration:
                pass
        return True

    def click_mouse(self, button: int, modifiers: int) -> None:
        """Used for testing, to simulate pressing and releasing a mouse
        button."""
        self.on_mouse_press(0, 0, button, modifiers)
        self.on_mouse_release(0, 0, button, modifiers)

    def before_run(self) -> None:
        """This hook is called by the run method, just before pyglet.app.run is
        called.

        By this point, default events have been decorated, such as
        on_key_press, and on_text. Also, we are inside a synthizer.initialized
        context manager, so feel free to play sounds."""
        pass

    def run(self, window: Window, mouse_exclusive: bool = True) -> None:
        """Run the game."""
        pyglet.options['shadow_window'] = False
        window.push_handlers(self)
        window.set_exclusive_mouse(mouse_exclusive)
        self.window = window
        with initialized():
            self.before_run()
            app.run()

    def push_level(self, level: Level) -> None:
        """Push a level onto self.levels."""
        self.levels.append(level)
        if self.window is not None:
            self.window.push_handlers(level)
        level.on_push()

    def replace_level(self, level: Level) -> None:
        """Pop the current level, then push the new one."""
        self.pop_level()
        self.push_level(level)

    def pop_level(self) -> None:
        """Pop the most recent level from the stack."""
        level: Level = self.levels.pop()
        if self.window is not None:
            self.window.pop_handlers()
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

    def on_close(self) -> None:
        """The window is closing."""
        self.clear_levels()
