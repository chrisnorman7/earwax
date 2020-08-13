"""Provides the Menu class."""

from time import time
from typing import Callable, List, Optional

from attr import Factory, attrs
from pyglet.window import key

from ..action import ActionFunctionType, OptionalGenerator
from ..level import DismissibleMixin, Level, TitleMixin
from ..speech import tts
from .menu_item import MenuItem


@attrs(auto_attribs=True)
class Menu(TitleMixin, DismissibleMixin, Level):
    """A menu which holds multiple menu items which can be activated using
    actions."""

    # The list of MenuItem instances for this menu.
    items: List[MenuItem] = Factory(list)

    # The user's position in this menu.
    position: int = -1

    # The maximum time between menu searches.
    search_timeout: float = 0.5

    # The time the last menu search was performed.
    search_time: float = 0.0

    # The current menu search search string.
    search_string: str = ''

    def __attrs_post_init__(self) -> None:
        """Initialise the menu."""
        self.action('Activate item', symbol=key.RETURN)(self.activate)
        self.action('Dismiss', symbol=key.ESCAPE)(self.dismiss)
        self.action('Move down', symbol=key.DOWN)(self.move_down)
        self.action('Move up', symbol=key.UP)(self.move_up)
        self.motion(key.MOTION_BEGINNING_OF_LINE)(self.home)
        self.motion(key.MOTION_END_OF_LINE)(self.end)

    @property
    def current_item(self) -> Optional[MenuItem]:
        """Return the currently selected menu item. If position is -1, return
        None."""
        if self.position != -1:
            return self.items[self.position]
        return None

    def item(self, title: str) -> Callable[[ActionFunctionType], MenuItem]:
        """Decorate a function to be used as a menu item."""

        def inner(func: ActionFunctionType) -> MenuItem:
            """Actually add the function."""
            return self.add_item(title, func)

        return inner

    def add_item(self, title: str, func: 'ActionFunctionType') -> MenuItem:
        """Add an item to this menu. All arguments are passed to the
        constructor of MenuItem."""
        menu_item: MenuItem = MenuItem(title, func)
        self.items.append(menu_item)
        return menu_item

    def show_selection(self) -> None:
        """Speak the menu item at the current position, or the title of this
        menu, if position is -1.

        This function performs no error checking, so it will happily throw
        errors if self.position is something stupid."""
        item: Optional[MenuItem] = self.current_item
        if item is None:
            tts.speak(self.title)
        else:
            tts.speak(item.title)
            item.on_selected()

    def move_up(self) -> None:
        """Move up in this menu."""
        self.position = max(-1, self.position - 1)
        self.show_selection()

    def move_down(self) -> None:
        """Move down in this menu."""
        self.position = min(len(self.items) - 1, self.position + 1)
        self.show_selection()

    def activate(self) -> OptionalGenerator:
        """Activate the currently focused menu item."""
        if self.current_item is None:
            return None
        return self.current_item.func()

    def home(self) -> None:
        """Move to the start of a menu."""
        self.position = 0
        self.show_selection()

    def end(self) -> None:
        """Move to the end of a menu."""
        self.position = len(self.items) - 1
        self.show_selection()

    def on_text(self, text: str) -> None:
        """Search this menu."""
        now: float = time()
        if (now - self.search_time) > self.search_timeout:
            self.search_string = text.lower()
        else:
            self.search_string += text.lower()
        self.search_time = now
        index: int
        item: MenuItem
        for index, item in enumerate(self.items):
            if item.title.lower().startswith(self.search_string):
                self.position = index
                self.show_selection()
                break

    def on_push(self) -> None:
        """Show the current selection. That will be the same as speaking the
        title, unless the initial focus has been set."""
        self.show_selection()

    def on_reveal(self) -> None:
        """Show the current selection."""
        self.show_selection()
