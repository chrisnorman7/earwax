"""Provides the Game class."""

from inspect import isgenerator
from typing import Callable, Dict, Generator, Iterator, List, Optional, cast

from attr import Factory, attrib, attrs
from pyglet import app, clock, options
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
    on_key_release_generators: ReleaseGeneratorListType = attrib(
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
                        self.on_key_release_generators[symbol] = cast(
                            Generator[None, None, None], res
                        )
        return True

    def on_key_release(self, symbol: int, modifiers: int) -> bool:
        """A key has been released."""
        a: Action
        for a in self.triggered_actions:
            if a.symbol == symbol:
                self.stop_action(a)
        if symbol in self.on_key_release_generators:
            generator: Generator[
                None, None, None
            ] = self.on_key_release_generators.pop(symbol)
            try:
                next(generator)
            except StopIteration:
                pass
        return True

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

    def on_text(self, text: str) -> bool:
        """If we have a level, call its on_text method. Otherwise, do
        nothing."""
        if self.level is not None:
            return self.level.on_text(text)
        return False

    def on_text_motion(self, motion: int) -> bool:
        """Handle a motion event."""
        if self.level is not None and motion in self.level.motions:
            self.level.motions[motion]()
            return True
        return False
