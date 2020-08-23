"""Provides the Game class."""

from inspect import isgenerator
from typing import Callable, Dict, Generator, Iterator, List, Optional, cast

import pyglet
from attr import Factory, attrib, attrs
from pyglet import app, clock
from pyglet.window import Window
from synthizer import initialized

from .action import Action, OptionalGenerator
from .event_matcher import EventMatcher
from .level import Level

ActionListType = List[Action]
ReleaseGeneratorListType = Dict[int, Generator[None, None, None]]
MotionFunctionType = Callable[[], None]
MotionsType = Dict[int, MotionFunctionType]


@attrs(auto_attribs=True, repr=False)
class Game:
    """The main game object.

    This object holds a reference to the game window, as well as a list of
    Level instances.

    Instances of the Level class can be pushed, popped, and replaced. The
    entire stack can also be cleared.

    Although it doesn't matter in what order you create objects, a `Game`
    instance is necessary for :class:`~earwax.Level` instances - and subclasses
    thereof - to be useful.

    :ivar ~earwax.Game.window: The pyglet window used to display the game.

    :ivar ~earwax.Game.levels: All the pushed levels.

    :ivar ~earwax.Game.triggered_actions: The currently triggered actions.

    :ivar ~earwax.Game.key_release_generators: The actions which returned
        generators, and need to do something on key release.

    :ivar ~earwax.Game.mouse_release_generators: The actions which returned
        generators, and need to do something on mouse release.

    :ivar ~earwax.Game.event_matchers: The event matchers used by this object.

        To take advantage of the pyglet events system, subclass
        :class:`earwax.Game`, or :class:`earwax.Level`, and include events from
        the `Pyglet documentation <https://pyglet.readthedocs.io/en/latest/>`_.
    """

    window: Optional[Window] = attrib(
        default=Factory(lambda: None), init=False
    )
    levels: List[Level] = attrib(default=Factory(list), init=False)
    triggered_actions: 'ActionListType' = attrib(
        default=Factory(list), init=False
    )
    key_release_generators: ReleaseGeneratorListType = attrib(
        default=Factory(dict), init=False
    )
    mouse_release_generators: ReleaseGeneratorListType = attrib(
        default=Factory(dict), init=False
    )
    event_matchers: Dict[str, EventMatcher] = attrib(
        default=Factory(dict), init=False, repr=False
    )

    def start_action(self, a: Action) -> OptionalGenerator:
        """Start an action. If the action has no interval, it will be ran
        straight away. Otherwise, it will be added to triggered_actions, and
        only ran if enough time has elapsed since the last run.

        This method is used when a trigger fires - such as a mouse button or
        key sequence being pressed - that triggers an action."""
        if a.interval is not None:
            self.triggered_actions.append(a)
            clock.schedule_interval(a.run, a.interval)
        return a.run(None)

    def stop_action(self, a: Action) -> None:
        """Unschedule an action, and remove it from triggered_actions.

        This method is called when the user stops doing something that
        previously triggered an action, such as releasing a key or a mouse
        button."""
        self.triggered_actions.remove(a)
        clock.unschedule(a.run)

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """A key has been pressed down.

        This is the default event that is used by `pyglet.window.Window`.

        By default it iterates through :attr:`self.level.actions
        <earwax.Level.actions>`, and searches for events that match the given
        symbol and modifiers."""
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
        """A key has been released.

        This is the default event that is used by `pyglet.window.Window`."""
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
        """A mouse button has been pressed down.

        This is the default event that is used by `pyglet.window.Window`.

By default, this method pretty much acts the same as
:meth:`~earwax.Game.on_key_press`, except it checks the discovered actions for
mouse buttons, rather than symbols."""
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
        """A mouse button has been released.

        This is the default event that is used by `pyglet.window.Window`.

        By default, this method is pretty much the same as
        :meth:`~earwax.Game.on_key_release`, except that it uses the
        discovered actions mouse button information."""
        a: Action
        for a in self.triggered_actions:
            if a.mouse_button == button:
                self.stop_action(a)
        if button in self.mouse_release_generators:
            generator: Generator[
                None, None, None
            ] = self.mouse_release_generators.pop(button)
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
        """This hook is used by the run method, just before pyglet.app.run is
        called.

        By this point, default events have been decorated, such as
        on_key_press and on_text. Also, we are inside a synthizer.initialized
        context manager, so feel free to play sounds."""
        pass

    def run(self, window: Window, mouse_exclusive: bool = True) -> None:
        """Run the game.

        By default, this method will perform the following actions in order:

        * disable pyglet's shadow window, which can cause problems with screen
            readers.

        * Iterate over all the found event types on `pyglet.window.Window`, and
            decorate them with :class:`~earwax.EventMatcher` instances. This
            means :class:`~earwax.Game` and :class:`~earwax.Level` subclasses
            can take full advantage of all event types by simply adding methods
            with the correct names to their classes.

        * Set the requested mouse exclusive mode on the provided window.

        * Enter a `synthizer.initialized` contextmanager.

        * Call the :meth:`~earwax.Game.before_run` method.

        * Start the pyglet event loop.
        """
        pyglet.options['shadow_window'] = False
        name: str
        em: EventMatcher
        for name in window.event_types:
            em = EventMatcher(self, name)
            self.event_matchers[name] = em
            window.event(name)(em.dispatch)
        window.set_exclusive_mouse(mouse_exclusive)
        self.window = window
        with initialized():
            self.before_run()
            app.run()

    def push_level(self, level: Level) -> None:
        """Push a level onto self.levels.

        This ensures that all events will be handled by the provided level
        until another level is pushed on top, or the current one is popped.

        This method also calls :meth:`~earwax.Level.on_push` on the provided
        level."""
        self.levels.append(level)
        level.on_push()

    def replace_level(self, level: Level) -> None:
        """Pop the current level, then push the new one.

        This method uses :meth:`~earwax.Game.pop_level`, and
        :meth:`~earwax.Game.push_level`, so make sure you familiarise yourself
        with what methods will be called on each level."""
        self.pop_level()
        self.push_level(level)

    def pop_level(self) -> None:
        """Pop the most recent level from the stack.

        If there is a level underneath the current one, then events will be
        passed to it. Otherwise there will be an empty stack, and events won't
        get handled.

        This method calls :meth:`~earwax.Level.on_pop` on the popped level, and
        :meth:`~earwax.Level.on_reveal` on the one below it."""
        level: Level = self.levels.pop()
        level.on_pop()
        if self.level is not None:
            self.level.on_reveal()

    def clear_levels(self) -> None:
        """Pop all levels.

        The :meth:`earwax.Level.on_pop` method will be called on every level
        that is popped."""
        while self.levels:
            self.pop_level()

    @property
    def level(self) -> Optional[Level]:
        """Get the most recently added level.

        If the stack is empty, None will be returned."""
        if len(self.levels):
            return self.levels[-1]
        return None

    def on_close(self) -> None:
        """Called when the window is closing.

        This is the default event that is used by `pyglet.window.Window`.

        By default, this method calls :meth:`self.clear_levels()
        <earwax.Game.clear_levels>`, to ensure any cleanup code is called."""
        self.clear_levels()
