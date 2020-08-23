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
    actions.

    As menus are simply :class:`~earwax.level.Level` subclasses, they can be
    :meth:`pushed <earwax.game.Game.push_level>`, :meth:`popped
    <earwax.game.Game.pop_level>`, and :meth:`replaced
    <earwax.game.Game.replace_level>`.

    To add items to a menu, you can either use the :meth:`item` decorator, or
    the :meth:`add_item` function.

    Here is an example of both methods::

        from earwax import Game, Level, Menu, tts
        from pyglet.window import key, Window
        w = Window(caption='Test Game')
        g = Game()
        l = Level()
        @l.action('Show menu', symbol=key.M)
        def menu():
            '''Show a menu with 2 items.'''
            m = Menu('Menu', g)
            @m.item('First Item')
            def first_item():
                tts.speak('First menu item.')
                g.pop_level()
            def second_item():
                tts.speak('Second menu item.')
                g.pop_level()
            m.add_item('Second Item', second_item)
            g.push_level(m)

        g.push_level(l)
        g.run(w)

    To override the default actions that are added to a menu, subclass
    :class:`earwax.Menu`, and override :meth:`__attrs_post_init__`.

    :ivar ~earwax.Menu.items: The list of MenuItem instances for this menu.

    :ivar ~earwax.Menu.position: The user's position in this menu.

    :ivar ~earwax.Menu.search_timeout: The maximum time between menu searches.

    :ivar ~earwax.Menu.search_time: The time the last menu search was
        performed.

    :ivar ~earwax.Menu.search_string: The current menu search search string.
    """

    items: List[MenuItem] = Factory(list)
    position: int = -1
    search_timeout: float = 0.5
    search_time: float = 0.0
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
        """Decorate a function to be used as a menu item.

        For example::

            @menu.item('Title')
            def func():
                pass

        If you don't want to use a decorator, you can use the
        :meth:`~earwax.Menu.add_item` method instead.
        """

        def inner(func: ActionFunctionType) -> MenuItem:
            """Actually add the function."""
            return self.add_item(title, func)

        return inner

    def add_item(self, title: str, func: 'ActionFunctionType') -> MenuItem:
        """Add an item to this menu.

        For example::

            m = Menu('Example Menu')
            def f():
                tts.speak('Menu item activated.')
            m.add_item('Test Item', f)

        If you would rather use decorators, use the :meth:`~earwax.Menu.item`
        method instead.
        """
        menu_item: MenuItem = MenuItem(title, func)
        self.items.append(menu_item)
        return menu_item

    def show_selection(self) -> None:
        """Speak the menu item at the current position, or the title of this
        menu, if position is -1.

        This function performs no error checking, so it will happily throw
        errors if :attr:`position` is something stupid."""
        item: Optional[MenuItem] = self.current_item
        if item is None:
            tts.speak(self.title)
        else:
            tts.speak(item.title)
            item.on_selected()

    def move_up(self) -> None:
        """Move up in this menu.

        Usually triggered by the up arrow key."""
        self.position = max(-1, self.position - 1)
        self.show_selection()

    def move_down(self) -> None:
        """Move down in this menu.

        Usually triggered by the down arrow key."""
        self.position = min(len(self.items) - 1, self.position + 1)
        self.show_selection()

    def activate(self) -> OptionalGenerator:
        """Activate the currently focused menu item.

    Usually triggered by the enter key."""
        if self.current_item is None:
            return None
        return self.current_item.func()

    def home(self) -> None:
        """Move to the start of a menu.

        Usually triggered by the home key."""
        self.position = 0
        self.show_selection()

    def end(self) -> None:
        """Move to the end of a menu.

        Usually triggered by the end key."""
        self.position = len(self.items) - 1
        self.show_selection()

    def on_text(self, text: str) -> None:
        """Handle sent text.

        By default, performs a search of this menu."""
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
        """This object has been pushed onto a :class:`~earwax.game.Game` instance.

        Show the current selection. That will be the same as speaking the
        title, unless the initial focus has been set."""
        self.show_selection()
