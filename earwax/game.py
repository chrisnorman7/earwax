"""Provides the Game class."""

from inspect import isgenerator
from time import time
from typing import (TYPE_CHECKING, Callable, Dict, Generator, Iterator, List,
                    Optional, cast)

from attr import Factory, attrib, attrs
from pyglet import app, clock, options
from pyglet.window import Window, key

from synthizer import initialized

from .action import ActionFunctionType, Action
if TYPE_CHECKING:
    from .editor import Editor
    from .menu import Menu, MenuItem
from .speech import tts

ActionListType = List[Action]
ReleaseGeneratorListType = Dict[int, Generator[None, None, None]]
MenuListType = List['Menu']


@attrs(auto_attribs=True)
class Game:
    """The main game object.

    Although things like menus can be used without a Game object, this object
    is central to pretty much everything else."""

    # The title of the window that will be created.
    title: str

    # A list of actions which can be called from within the game.
    actions: ActionListType = attrib(default=Factory(list), init=False)

    # The currently triggered actions.
    triggered_actions: 'ActionListType' = attrib(
        default=Factory(list), init=False
    )

    # The actions which returned generators, and need to do something on key
    # release.
    on_key_release_generators: ReleaseGeneratorListType = attrib(
        default=Factory(dict), init=False
    )

    # The window to display the game.
    window: Optional[Window] = attrib(
        default=Factory(lambda: None), init=False
    )

    # The current menus (if any).
    menus: MenuListType = attrib(default=Factory(list), init=False)

    # The time the last menu search was performed.
    menu_search_time: float = attrib(Factory(float), init=False)

    # The timeout for menu searches.
    menu_search_timeout: float = Factory(lambda: 0.5)

    # The current menu search search string.
    menu_search_string: str = attrib(Factory(str), init=False)

    # The current editor.
    editor: Optional['Editor'] = attrib(
        default=Factory(lambda: None), init=False
    )

    def start_action(self, a: Action) -> Optional[
        Generator[None, None, None]
    ]:
        """Start an action. If the action has no interval, it will be ran
        straight away. Otherwise, it will be added to triggered_actions."""
        if a.interval is None:
            return a.run(None)
        else:
            self.triggered_actions.append(a)
            a.run(None)
            clock.schedule_interval(a.run, a.interval)
            return None

    def stop_action(self, a: Action) -> None:
        """Unschedule an action, and remove it from triggered_actions."""
        self.triggered_actions.remove(a)
        clock.unschedule(a.run)

    def on_key_press(self, symbol: int, modifiers: int) -> bool:
        """A key has been pressed down."""
        a: Action
        for a in self.actions:
            if a.symbol == symbol and a.modifiers == modifiers:
                res: Optional[
                    Generator[None, None, None]
                ] = self.start_action(a)
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

    def on_text(self, text: str) -> None:
        """Enter text into the current editor."""
        if self.editor is not None:
            return self.editor.on_text(text)
        elif self.menu is not None:
            now: float = time()
            if (now - self.menu_search_time) > self.menu_search_timeout:
                self.menu_search_string = text.lower()
            else:
                self.menu_search_string += text.lower()
            self.menu_search_time = now
            index: int
            item: 'MenuItem'
            for index, item in enumerate(self.menu.items):
                if item.title.lower().startswith(self.menu_search_string):
                    self.menu.position = index
                    self.menu.show_selection()
                    break

    def on_text_motion(self, motion: int) -> None:
        """Pass the motion onto any attached editor."""
        if self.editor is not None:
            return self.editor.on_text_motion(motion)

    def before_run(self) -> None:
        """This hook is called by the run method, just before pyglet.app.run is
        called.

        By this point, default events have been decorated, such as
        on_key_press, and on_text. Also, we are inside a synthizer.initialized
        context manager, so feel free to play sounds."""
        pass

    def run(self) -> None:
        """Run the game."""
        options['shadow_window'] = False
        self.window = Window(caption=self.title)
        self.window.event(self.on_key_press)
        self.window.event(self.on_key_release)
        self.window.event(self.on_text)
        self.window.event(self.on_text_motion)
        with initialized():
            self.before_run()
            app.run()

    def action(self, name: str, **kwargs) -> Callable[
        [ActionFunctionType], Action
    ]:
        """A decorator to add an action to this game."""

        def inner(func: ActionFunctionType) -> Action:
            """Actually add the action."""
            a: Action = Action(self, name, func, **kwargs)
            self.actions.append(a)
            return a

        return inner

    def no_menu(self) -> bool:
        """Returns True if there are no menus."""
        return len(self.menus) == 0

    def no_editor(self) -> bool:
        """Returns true if there is no editor."""
        return self.editor is None

    def normal(self) -> bool:
        """Returns True if both no_menu and no_editor are True."""
        return all([self.no_menu(), self.no_editor()])

    def push_menu(self, menu: 'Menu') -> None:
        """Push a menu onto self.menus."""
        self.menus.append(menu)
        menu.show_selection()

    def replace_menu(self, menu: 'Menu') -> None:
        """Pop the current menu, then push the new one."""
        self.pop_menu()
        self.push_menu(menu)

    def pop_menu(self) -> None:
        """Pop the most recent menu from the stack."""
        self.menus.pop()
        if not self.no_menu:
            self.menus[-1].show_selection()

    def clear_menus(self) -> None:
        """Pop all menus."""
        self.menus.clear()

    @property
    def menu(self) -> Optional['Menu']:
        """Get the most recently added menu."""
        if len(self.menus):
            return self.menus[-1]
        return None

    def menu_activate(self) -> Optional[Generator[None, None, None]]:
        """Activate a menu item."""
        if self.menu is not None:
            return self.menu.activate()
        return None

    def dismiss(self) -> None:
        """Dismiss the currently active menu."""
        if self.menu is not None and self.menu.dismissible:
            self.pop_menu()
        elif self.editor is not None and self.editor.dismissible:
            self.editor = None
        else:
            return
        tts.speak('Cancel.')

    def menu_up(self) -> None:
        """Move up in a menu."""
        if self.menu is not None:
            self.menu.move_up()

    def menu_down(self) -> None:
        """Move down in a menu."""
        if self.menu is not None:
            self.menu.move_down()

    def menu_home(self) -> None:
        """Move to the start of a menu."""
        if self.menu is not None:
            self.menu.position = 0
            self.menu.show_selection()

    def menu_end(self) -> None:
        """Move to the end of a menu."""
        if self.menu is not None:
            self.menu.position = len(self.menu.items) - 1
            self.menu.show_selection()

    def submit_editor(self) -> None:
        """Submit the text in an editor."""
        if self.editor is not None:
            self.editor.submit()

    def clear_editor(self) -> None:
        """Clear the text in an editor."""
        if self.editor is not None:
            self.editor.clear()

    def add_default_actions(self) -> None:
        """Add actions relating to menus and editors."""
        self.actions.extend(
            [
                Action(
                    self, 'Activate menu item', self.menu_activate,
                    symbol=key.RETURN, can_run=lambda: getattr(
                        self.menu, 'position', -1
                    ) != -1 and self.editor is None
                ),
                Action(
                    self, 'Exit from a menu or editor', self.dismiss,
                    symbol=key.ESCAPE, can_run=lambda: True
                ),
                Action(
                    self, 'Move up in a menu', self.menu_up, symbol=key.UP,
                    can_run=lambda: not self.no_menu() and self.editor is None
                ),
                Action(
                    self, 'Move down in a menu', self.menu_down,
                    symbol=key.DOWN, can_run=lambda: not self.no_menu()
                    and self.editor is None
                ),
                Action(
                    self, 'Move to the start of a menu', self.menu_home,
                    symbol=key.HOME, can_run=lambda: not self.no_menu()
                ),
                Action(
                    self, 'Move to the end of a menu', self.menu_end,
                    symbol=key.END, can_run=lambda: not self.no_menu()
                ),
                Action(
                    self, 'Submit editor', self.submit_editor,
                    symbol=key.RETURN, can_run=lambda: not self.no_editor()
                ),
                Action(
                    self, 'Clear editor', self.clear_editor, symbol=key.U,
                    modifiers=key.MOD_CTRL,
                    can_run=lambda: not self.no_editor()
                )
            ]
        )
