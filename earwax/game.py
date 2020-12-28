"""Provides the Game class."""

from concurrent.futures import Executor, ThreadPoolExecutor
from inspect import isgenerator
from pathlib import Path
from typing import (
    Callable, Dict, Generator, Iterator, List, Optional, Tuple, Type, cast)
from warnings import warn

from attr import Factory, attrib, attrs

from .credit import Credit
from .menu.action_menu import ActionMenu
from .task import IntervalFunction, Task, TaskFunction
from .types import EventType

try:
    from synthizer import Context, DirectSource, Source, initialized
except ModuleNotFoundError:
    Context, DirectSource, Source, initialized = (None, None, None, None)

try:
    from cytolk.tolk import detect_screen_reader, load, unload
    from pyglet import app, clock
    from pyglet.input import Joystick, get_joysticks
    from pyglet.resource import get_settings_path
    from pyglet.window import Window
except ModuleNotFoundError:
    detect_screen_reader = None
    load = None
    unload = None
    app = None
    clock = None
    Joystick = None
    get_joysticks = None
    get_settings_path = None
    Window = None

from .action import Action, HatDirection, OptionalGenerator
from .configuration import EarwaxConfig
from .event_matcher import EventMatcher
from .hat_directions import DEFAULT
from .level import Level
from .mixins import RegisterEventMixin
from .sound import SoundManager
from .speech import tts
from .types import (ActionListType, JoyButtonReleaseGeneratorDictType,
                    ReleaseGeneratorDictType)

NoneType: Type[None] = type(None)


class GameNotRunning(Exception):
    """This game is not running."""


@attrs(auto_attribs=True, repr=False)
class Game(RegisterEventMixin):
    """The main game object.

    This object holds a reference to the game window, as well as a list of
    Level instances.

    In addition, references to various parts of the audio subsystem reside on
    this object, namely :attr:`~earwax.Game.audio_context`.

    Instances of the Level class can be pushed, popped, and replaced. The
    entire stack can also be cleared.

    Although it doesn't matter in what order you create objects, a ``Game``
    instance is necessary for :class:`~earwax.Level` instances - and subclasses
    thereof - to be useful.

    :ivar ~earwax.Game.window: The pyglet window used to display the game.

    :ivar ~earwax.Game.config: The configuration object used by this game.

    :ivar ~earwax.game.name: The name of this game. Used by
        :meth:`~earwax.Game.get_settings_path`.

    :ivar ~earwax.Game.audio_context: The Synthizer context to route audio
        through.

    :ivar ~earwax.Game.interface_sound_manager: A sound manager for playing
        interface sounds.

    :ivar ~earwax.Game.music_sound_manager: A sound manager for playing music.

    :ivar ~earwax.Game.ambiance_sound_manager: A sound manager for playing
        ambiances.

    :ivar ~earwax.Game.levels: All the pushed :class:`earwax.Level` instances.

    :ivar ~earwax.Game.triggered_actions: The currently triggered
        :class:`earwax.Action` instances.

    :ivar ~earwax.Game.key_release_generators: The :class:`earwax.Action`
        instances which returned generators, and need to do something on key
        release.

    :ivar ~earwax.Game.mouse_release_generators: The :class:`earwax.Action`
        instances which returned generators, and need to do something on mouse
        release.

    :ivar ~earwax.Game.joybutton_release_generators: The :class:`earwax.Action`
        instances which returned generators, and need to do something on
        joystick button release.

    :ivar ~earwax.Game.event_matchers: The :class:`earwax.EventMatcher`
        instances used by this object.

        To take advantage of the pyglet events system, subclass
        :class:`earwax.Game`, or :class:`earwax.Level`, and include events from
        `pyglet.window.Window
        <https://pyglet.readthedocs.io/en/latest/modules/window.html>`_.

    :ivar ~earwax.Game.joysticks: The list of joysticks that have been opened
        by this instance.

    :ivar ~earwax.Game.thread_pool: An instance of ``ThreadPoolExecutor`` to
        use for threaded operations.

    :ivar ~earwax.Game.tasks: A list of :class:`earwax.Task` instances.

        You can add tasks with the :meth:`~earwax.Game.register_task`
        decorator, and remove them again with the
        :meth:`~earwax.Game.remove_task` method.
    """

    name: str = __name__

    window: Optional[Window] = attrib(
        default=Factory(NoneType), init=False, repr=False
    )
    config: EarwaxConfig = attrib(
        default=Factory(EarwaxConfig), init=False, repr=False
    )
    audio_context: Optional[Context] = attrib(
        default=Factory(NoneType), repr=False
    )

    interface_sound_manager: SoundManager = attrib(
        default=Factory(NoneType), init=False, repr=False
    )
    music_sound_manager: Optional[SoundManager] = attrib(
        default=Factory(NoneType), init=False, repr=False
    )
    ambiance_sound_manager: Optional[SoundManager] = attrib(
        default=Factory(NoneType), init=False, repr=False
    )

    levels: List[Level] = attrib(default=Factory(list), init=False)

    triggered_actions: 'ActionListType' = attrib(
        default=Factory(list), init=False
    )

    key_release_generators: ReleaseGeneratorDictType = attrib(
        default=Factory(dict), init=False
    )

    mouse_release_generators: ReleaseGeneratorDictType = attrib(
        default=Factory(dict), init=False
    )

    joybutton_release_generators: JoyButtonReleaseGeneratorDictType = attrib(
        default=Factory(dict), init=False
    )

    joyhat_release_generators: List[Generator[None, None, None]] = attrib(
        default=Factory(list), init=False
    )

    event_matchers: Dict[str, EventMatcher] = attrib(
        default=Factory(dict), init=False, repr=False
    )

    joysticks: List[Joystick] = attrib(default=Factory(list), init=False)

    thread_pool: Executor = attrib(
        default=Factory(ThreadPoolExecutor), repr=False
    )

    tasks: List[Task] = attrib(default=Factory(list), init=False, repr=False)
    credits: List[Credit] = attrib(default=Factory(list), repr=False)

    def __attrs_post_init__(self) -> None:
        """Register default events."""
        for func in (
            self.before_run, self.after_run, self.on_close,
            self.on_joyhat_motion, self.on_joybutton_press,
            self.on_joybutton_release, self.on_key_press, self.on_key_release,
            self.on_mouse_press, self.on_mouse_release
        ):
            self.register_event(cast(EventType, func))

    def start_action(self, a: Action) -> OptionalGenerator:
        """Start an action.

        If the action has no interval, it will be ran
        straight away. Otherwise, it will be added to
        :attr:`self.triggered_actions <earwax.Game.triggered_actions>`, and
        only ran if enough time has elapsed since the last run.

        This method is used when a trigger fires - such as a mouse button or
        key sequence being pressed - that triggers an action.

        :param a: The :class:`earwax.Action` instance that should be started.
        """
        if a.interval is not None:
            self.triggered_actions.append(a)
            clock.schedule_interval(a.run, a.interval)
        return a.run(None)

    def stop_action(self, a: Action) -> None:
        """Unschedule an action.

        The provided action will be removed from
        :attr:`~earwax.Game.triggered_actions`.

        This method is called when the user stops doing something that
        previously triggered an action, such as releasing a key or a mouse
        button

        :param a: The :class:`earwax.Action` instance that should be stopped.
        """
        self.triggered_actions.remove(a)
        clock.unschedule(a.run)

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """Handle a pressed key.

        This is the default event that is used by ``pyglet.window.Window``.

        By default it iterates through :attr:`self.level.actions
        <earwax.Level.actions>`, and searches for events that match the given
        symbol and modifiers.

        :param symbol: One of the key constants from `pyglet.window.key
            <https://pythonhosted.org/pyglet/api/pyglet.window.key-
            module.html>`__.

        :param modifiers: One of the modifier constants from `pyglet.window.key
            <https://pythonhosted.org/pyglet/api/pyglet.window.key-
            module.html>`__.
        """
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
        """Handle a released key.

        This is the default event that is used by ``pyglet.window.Window``.

        :param symbol: One of the key constants from `pyglet.window.key
            <https://pythonhosted.org/pyglet/api/pyglet.window.key-
            module.html>`__.

        :param modifiers: One of the modifier constants from `pyglet.window.key
            <https://pythonhosted.org/pyglet/api/pyglet.window.key-
            module.html>`__.
        """
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
        """Simulate a key press.

        This method is used in tests.

        First presses the given key combination, then releases it.

        If string and motion are not None, then on_text, and on_text_motion
        events will also be fired.

        :param symbol: One of the key constants from `pyglet.window.key
            <https://pythonhosted.org/pyglet/api/pyglet.window.key-
            module.html>`__.

        :param modifiers: One of the modifier constants from `pyglet.window.key
            <https://pythonhosted.org/pyglet/api/pyglet.window.key-
            module.html>`__.

        :param string: A string to be picked up by an ``on_text`` event
            handler..

        :param motion: A key to be picked up by an ``on_text_motion`` event
            handler.
        """
        self.on_key_press(symbol, modifiers)
        if string is not None:
            getattr(self, 'on_text', lambda s: None)(string)
        if motion is not None:
            getattr(self, 'on_text_motion', lambda m: None)(motion)
        self.on_key_release(symbol, modifiers)

    def on_mouse_press(
        self, x: int, y: int, button: int, modifiers: int
    ) -> bool:
        """Handle a mouse button press.

        This is the default event that is used by ``pyglet.window.Window``.

        By default, this method pretty much acts the same as
        :meth:`~earwax.Game.on_key_press`, except it checks the discovered
        actions for mouse buttons, rather than symbols.

        :param x: The x coordinate of the mouse.

        :param y: The y coordinate of the mouse.

        :param button: One of the mouse button constants from
            `pyglet.window.mouse <https://pythonhosted.org/pyglet/api/
            pyglet.window.mouse-module.html>`__.

        :param modifiers: One of the modifier constants from `pyglet.window.key
            <https://pythonhosted.org/pyglet/api/pyglet.window.key-
            module.html>`__.
        """
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
        """Handle a mouse button release.

        This is the default event that is used by ``pyglet.window.Window``.

        By default, this method is pretty much the same as
        :meth:`~earwax.Game.on_key_release`, except that it uses the
        discovered actions mouse button information.

        :param x: The x coordinate of the mouse.

        :param y: The y coordinate of the mouse.

        :param button: One of the mouse button constants from
            `pyglet.window.mouse <https://pythonhosted.org/pyglet/api/
            pyglet.window.mouse-module.html>`__.

        :param modifiers: One of the modifier constants from `pyglet.window.key
            <https://pythonhosted.org/pyglet/api/pyglet.window.key-
            module.html>`__.
        """
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
        """Simulate a mouse click.

        This method is used for testing, to simulate first pressing, then
        releasing a mouse button.

        :param button: One of the mouse button constants from
            `pyglet.window.mouse <https://pythonhosted.org/pyglet/api/
            pyglet.window.mouse-module.html>`__.

        :param modifiers: One of the modifier constants from
            `pyglet.window.key <https://pythonhosted.org/pyglet/api/
            pyglet.window.key-module.html>`__.
        """
        self.on_mouse_press(0, 0, button, modifiers)
        self.on_mouse_release(0, 0, button, modifiers)

    def on_joybutton_press(self, joystick: Joystick, button: int) -> bool:
        """Handle the press of a joystick button.

        This is the default handler that fires when a joystick button is
        pressed.

        :param joystick: The joystick that emitted the event.

        : param button: The button that was pressed.
        """
        if self.level is not None:
            a: Action
            for a in self.level.actions:
                if a.joystick_button == button:
                    res: OptionalGenerator = self.start_action(a)
                    if isgenerator(res):
                        next(cast(Iterator[None], res))
                        self.joybutton_release_generators[
                            (joystick.device.name, button)
                        ] = cast(
                            Generator[None, None, None], res
                        )
            return True
        return False

    def on_joybutton_release(self, joystick: Joystick, button: int) -> bool:
        """Handle the release of a joystick button.

        This is the default handler that fires when a joystick button is
        released.

        :param joystick: The joystick that emitted the event.

        : param button: The button that was pressed.
        """
        t: Tuple[str, int] = (joystick.device.name, button)
        a: Action
        for a in self.triggered_actions:
            if a.joystick_button == button:
                self.stop_action(a)
        if t in self.joybutton_release_generators:
            generator: Generator[
                None, None, None
            ] = self.joybutton_release_generators.pop(t)
            try:
                next(generator)
            except StopIteration:
                pass
        return True

    def on_joyhat_motion(self, joystick: Joystick, x: int, y: int) -> bool:
        """Handle joyhat motions.

        This is the default handler that fires when a hat is moved.

        If the given position is the default position ``(0, 0)``, then any
        actions started by hat motions are stopped.

        :param joystick: The joystick that emitted the event.

        : param x: The left / right position of the hat.

        : param y: The up / down position of the hat.
        """
        direction: HatDirection = (x, y)
        a: Action
        if direction == DEFAULT:
            for a in self.triggered_actions:
                if a.hat_direction is not None:
                    self.stop_action(a)
            generator: Generator[None, None, None]
            for generator in self.joyhat_release_generators:
                try:
                    next(generator)
                except StopIteration:
                    pass
            self.joyhat_release_generators.clear()
        if self.level is not None:
            for a in self.level.actions:
                if a.hat_direction == direction:
                    res: OptionalGenerator = self.start_action(a)
                    if isgenerator(res):
                        next(cast(Iterator[None], res))
                        self.joyhat_release_generators.append(
                            cast(Generator[None, None, None], res)
                        )
            return True
        return False

    def before_run(self) -> None:
        """Do stuff before starting the main event loop.

        This event is used by the run method, just before pyglet.app.run is
        called.

        By this point, default events have been decorated, such as
        on_key_press and on_text. Also, we are inside a synthizer.initialized
        context manager, so feel free to play sounds, and use
        :attr:`self.audio_context <earwax.Game.audio_context>`.
        """
        pass

    def after_run(self) -> None:
        """Run code before the game exits.

        This event is dispatched after the main game loop has ended.

        By this point, synthizer has been shutdown, and there is nothing else
        to be done.
        """
        pass

    def do_run(self, initial_level: Optional[Level]) -> None:
        """Really run the game."""
        source: Source = DirectSource(self.audio_context)
        manager: SoundManager = SoundManager(self.audio_context, source)
        manager.gain = self.config.sound.sound_volume.value
        self.interface_sound_manager = manager
        source = DirectSource(self.audio_context)
        manager = SoundManager(self.audio_context, source, should_loop=True)
        manager.gain = self.config.sound.music_volume.value
        self.music_sound_manager = manager
        source = DirectSource(self.audio_context)
        manager = SoundManager(self.audio_context, source, should_loop=True)
        manager.gain = self.config.sound.ambiance_volume.value
        self.ambiance_sound_manager = manager
        if initial_level is not None:
            self.push_level(initial_level)
        self.dispatch_event('before_run')
        app.run()

    def run(
        self, window: Window, mouse_exclusive: bool = True,
        initial_level: Optional[Level] = None
    ) -> None:
        """Run the game.

        By default, this method will perform the following actions in order:

        * Load cytolk.

        * Iterate over all the found event types on ``pyglet.window.Window``,
            and decorate them with :class:`~earwax.EventMatcher` instances.
            This means :class:`~earwax.Game` and :class:`~earwax.Level`
            subclasses can take full advantage of all event types by simply
            adding methods with the correct names to their classes.

        * Set the requested mouse exclusive mode on the provided window.

        * call :meth:`~earwax.Game.open_joysticks`.

        * Enter a ``synthizer.initialized`` contextmanager.

        * populate :attr:`~earwax.Game.interface_sound_manager`,
            :attr:`~earwax.Game.music_sound_manager`, and
            :attr:`~earwax.Game.ambiance_sound_manager`, and set the
            appropriate gains from :attr:`~earwax.Game.config`.

        * if ``initial_level`` is not ``None``, push the given level.

        * Dispatch the :meth:`~earwax.Game.before_run` event.

        * Start the pyglet event loop.

        * unload cytolk.

        :param window: The pyglet window that will form the game's interface.

        :param mouse_exclusive: The mouse exclusive setting for the window.

        :param initial_level: A level to push onto the stack.
        """
        name: str
        em: EventMatcher
        for name in window.event_types:
            em = EventMatcher(self, name)
            self.event_matchers[name] = em
            window.event(name)(em.dispatch)
        window.set_exclusive_mouse(mouse_exclusive)
        self.window = window
        self.open_joysticks()
        load()
        if detect_screen_reader() is None:
            warn('No screen reader detected.')
        if self.audio_context is None:
            with initialized():
                self.audio_context = Context()
                self.do_run(initial_level)
        else:
            self.do_run(initial_level)
        unload()
        self.dispatch_event('after_run')

    def open_joysticks(self) -> None:
        """Open and attach events to all attached joysticks."""
        j: Joystick
        for j in get_joysticks():
            if j in self.joysticks:
                continue
            j.open()
            self.joysticks.append(j)
            name: str
            for name in j.event_types:
                if name not in self.event_matchers:
                    self.event_matchers[name] = EventMatcher(self, name)
                m: EventMatcher = self.event_matchers[name]
                j.event(name)(m.dispatch)

    def push_level(self, level: Level) -> None:
        """Push a level onto :attr:`self.levels <earwax.Game.levels>`.

        This ensures that all events will be handled by the provided level
        until another level is pushed on top, or the current one is popped.

        This method also dispatches the :meth:`~earwax.Level.on_push` event on
        the provided level.

        If the old level is not None, then the ``on_cover`` event is dispatched
        on the old level, with the new level as the only argument.

        :param level: The :class:`earwax.Level` instance to push onto the
            stack.
        """
        if self.level is not None:
            self.level.dispatch_event('on_cover', level)
        self.levels.append(level)
        level.dispatch_event('on_push')

    def replace_level(self, level: Level) -> None:
        """Pop the current level, then push the new one.

        This method uses :meth:`~earwax.Game.pop_level`, and
        :meth:`~earwax.Game.push_level`, so make sure you familiarise yourself
        with what events will be called on each level.

        :param level: The :class:`earwax.Level` instance to push onto the
            stack.
        """
        self.pop_level()
        self.push_level(level)

    def pop_level(self) -> None:
        """Pop the most recent :class:`earwax.Level` instance from the stack.

        If there is a level underneath the current one, then events will be
        passed to it. Otherwise there will be an empty stack, and events won't
        get handled.

        This method calls :meth:`~earwax.Level.on_pop` on the popped level, and
        :meth:`~earwax.Level.on_reveal` on the one below it.
        """
        level: Level = self.levels.pop()
        level.dispatch_event('on_pop')
        if self.level is not None:
            self.level.dispatch_event('on_reveal')

    def clear_levels(self) -> None:
        """Pop all levels.

        The :meth:`earwax.Level.on_pop` method will be called on every level
        that is popped.
        """
        while self.levels:
            self.pop_level()

    @property
    def level(self) -> Optional[Level]:
        """Get the most recently added :class:`earwax.Level` instance.

        If the stack is empty, ``None`` will be returned.
        """
        if len(self.levels):
            return self.levels[-1]
        return None

    def on_close(self) -> None:
        """Run code when closing the window.

        Called when the window is closing.

        This is the default event that is used by ``pyglet.window.Window``.

        By default, this method calls :meth:`self.clear_levels()
        <earwax.Game.clear_levels>`, to ensure any clean up code is called.
        """
        self.clear_levels()

    def get_settings_path(self) -> Path:
        """Get a path to store game settings.

        Uses ``pyglet.resource.get_settings_path`` to get an appropriate
        settings path for this game.
        """
        return Path(get_settings_path(self.name))

    def output(self, text: str, interrupt: bool = False) -> None:
        """Output braille and / or speech.

        The earwax configuration is used to determine what should be outputted.

        :param text: The text to be spoken or output to a braille display.

        :param interrupt: If Whether or not to silence speech before outputting
            anything else.
        """
        if interrupt:
            tts.silence()
        if self.config.speech.speak.value:
            tts.speak(text)
        if self.config.speech.braille.value:
            tts.braille(text)

    def stop(self) -> None:
        """Close :attr:`self.window <earwax.Game.window>`.

        If ``self.window`` is ``None``, then :class:earwax.GameNotRunning` will
        be raised.
        """
        if self.window is None:
            raise GameNotRunning()
        self.window.dispatch_event('on_close')

    def register_task(
        self, interval: IntervalFunction
    ) -> Callable[[TaskFunction], Task]:
        """Decorate a function to use as a task.

        This function allows you to convert a function into a
        :class:`~earwax.Task` instance, so you can add tasks by decoration::

            @game.register_task(lambda: uniform(1.0, 5.0))
            def task(dt: float) -> None:
                '''A task.'''
                print('Working: %.2f.' % dt)
            task.start()

        :param interval: The function to use for the interval.
        """

        def inner(func: TaskFunction) -> Task:
            """Decorate the function."""
            t: Task = Task(interval, func)
            self.tasks.append(t)
            return t

        return inner

    def remove_task(self, task: Task) -> None:
        """Stop and remove a task.

        :param task: The task to be stopped.

            The task will first have its :meth:`~earwax.Task.stop` method
            called, then it will be removed from the :attr:`~earwax.Game.tasks`
            list.
        """
        task.stop()
        self.tasks.remove(task)

    def push_action_menu(self, title: str = 'Actions', **kwargs) -> ActionMenu:
        """Push and return an action menu.

        This method reduces the amount of code required to create a help menu::

            @level.action(
                'Help Menu', symbol=key.SLASH, modifiers=key.MOD_SHIFT
            )
            def help_menu() -> None:
                game.push_action_menu()

        :param title: The title of the new menu.

        :param kwargs: The extra keyword arguments to pass to the ActionMenu
            constructor.
        """
        menu: ActionMenu = ActionMenu(self, title, **kwargs)
        self.push_level(menu)
        return menu
