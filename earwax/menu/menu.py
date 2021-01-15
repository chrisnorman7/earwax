"""Provides the Menu class."""

import webbrowser
from inspect import isgenerator
from pathlib import Path
from time import time
from typing import TYPE_CHECKING, Callable, Generator, List, Optional

from attr import Factory, attrib, attrs

from ..action import ActionFunctionType, OptionalGenerator
from ..credit import Credit
from ..hat_directions import DOWN, LEFT, RIGHT, UP
from ..level import Level
from ..mixins import DismissibleMixin, TitleMixin
from ..pyglet import key
from ..sound import Sound
from .menu_item import MenuItem

if TYPE_CHECKING:
    from ..game import Game

YesNoFunction = Callable[[], OptionalGenerator]


@attrs(auto_attribs=True)
class Menu(Level, TitleMixin, DismissibleMixin):
    """A menu of :class:`~earwax.MenuItem` instances.

    Menus hold multiple menu items which can be activated using actions.

    As menus are simply :class:`~earwax.level.Level` subclasses, they can be
    :meth:`pushed <earwax.game.Game.push_level>`, :meth:`popped
    <earwax.game.Game.pop_level>`, and :meth:`replaced
    <earwax.game.Game.replace_level>`.

    To add items to a menu, you can either use the :meth:`item` decorator, or
    the :meth:`add_item` function.

    Here is an example of both methods::

        from earwax import Game, Level, Menu
        from pyglet.window import key, Window
        w = Window(caption='Test Game')
        g = Game()
        l = Level()
        @l.action('Show menu', symbol=key.M)
        def menu():
            '''Show a menu with 2 items.'''
            m = Menu(g, 'Menu')
            @m.item(title='First Item')
            def first_item():
                g.output('First menu item.')
                g.pop_level()
            def second_item():
                g.output('Second menu item.')
                g.pop_level()
            m.add_item(second_item, title='Second Item')
            g.push_level(m)

        g.push_level(l)
        g.run(w)

    To override the default actions that are added to a menu, subclass
    :class:`earwax.Menu`, and override :meth:`__attrs_post_init__`.

    :ivar ~earwax.Menu.item_sound_path: The default sound to play when moving
        through the menu.

        If the selected item's :attr:`~earwax.MenuItem.sound_path` attribute is
        not ``None``, then that value takes precedence.

    :ivar ~earwax.Menu.items: The list of MenuItem instances for this menu.

    :ivar ~earwax.Menu.position: The user's position in this menu.

    :ivar ~earwax.Menu.search_timeout: The maximum time between menu searches.

    :ivar ~earwax.Menu.search_time: The time the last menu search was
        performed.

    :ivar ~earwax.Menu.search_string: The current menu search search string.
    """

    item_select_sound_path: Optional[Path] = None
    item_activate_sound_path: Optional[Path] = None

    position: int = -1
    search_timeout: float = 0.5
    search_time: float = 0.0

    search_string: str = attrib(default=Factory(str), init=False)
    items: List[MenuItem] = attrib(default=Factory(list), init=False)
    select_sound: Optional[Sound] = attrib(
        default=Factory(type(None)), init=False, repr=False
    )

    def __attrs_post_init__(self) -> None:
        """Initialise the menu."""
        self.action('Activate item', symbol=key.RETURN, hat_direction=RIGHT)(
            self.activate
        )
        self.action('Dismiss', symbol=key.ESCAPE, hat_direction=LEFT)(
            self.dismiss
        )
        self.action('Move down', symbol=key.DOWN, hat_direction=DOWN)(
            self.move_down
        )
        self.action('Move up', symbol=key.UP, hat_direction=UP)(
            self.move_up
        )
        self.motion(key.MOTION_BEGINNING_OF_LINE)(self.home)
        self.motion(key.MOTION_END_OF_LINE)(self.end)
        self.register_event(self.on_text)
        super().__attrs_post_init__()

    @classmethod
    def from_credits(
        cls, game: 'Game', credits: List[Credit], title: str = 'Game Credits'
    ) -> 'Menu':
        """Return a menu for showing credits.

        :param game: The game to use.

        :param credits: The credits to show.

        :param title: The title of the new menu.
        """
        m: Menu = cls(game, title)
        credit: Credit
        for credit in credits:

            def func(url: str = credit.url) -> None:
                """Open the URL."""
                webbrowser.open(url)

            m.add_item(
                func, title=credit.name, select_sound_path=credit.sound,
                loop_select_sound=credit.loop
            )
        return m

    @classmethod
    def yes_no(
        cls, game: 'Game', yes_action: YesNoFunction, no_action: YesNoFunction,
        title: str = 'Are you sure?',
        yes_label: str = 'Yes', no_label: str = 'No',
        **kwargs
    ) -> 'Menu':
        """Create and return a yes no menu.

        :param game: The game to bind the new menu to.

        :param yes_action: The function to be called if the yes item is
            selected.

        :param no_action: The action to be performed if no is selected.

        :param title: The title of the menu.

        :param yes_label: The label of the yes item.

        :param no_label: The title of the no label.

        :param kwargs: Extra keyword arguments to be passed to the ``Menu``
            constructor.
        """
        m: Menu = cls(game, title, **kwargs)
        m.add_item(yes_action, title=yes_label)
        m.add_item(no_action, title=no_label)
        return m

    @property
    def current_item(self) -> Optional[MenuItem]:
        """Return the currently selected menu item.

        If position is -1, return
        ``None``.
        """
        if self.position != -1:
            return self.items[self.position]
        return None

    def item(self, **kwargs) -> Callable[[ActionFunctionType], MenuItem]:
        """Decorate a function to be used as a menu item.

        For example::

            @menu.item(title='Title')
            def func():
                pass

            @menu.item(sound_path=Path('sound.wav'))
            def item_with_sound():
                pass

        If you don't want to use a decorator, you can use the
        :meth:`~earwax.Menu.add_item` method instead.

        :param kwargs: Extra arguments to be passed to the constructor of
            :class:`earwax.MenuItem`.
        """

        def inner(func: ActionFunctionType) -> MenuItem:
            """Actually add the function."""
            return self.add_item(func, **kwargs)

        return inner

    def add_item(self, func: 'ActionFunctionType', **kwargs) -> MenuItem:
        """Add an item to this menu.

        For example::

            m = Menu(game, 'Example Menu')
            def f():
                game.output('Menu item activated.')
            m.add_item(f, title='Test Item')
            m.add_item(f, sound_path=Path('sound.wav'))

        If you would rather use decorators, use the :meth:`~earwax.Menu.item`
        method instead.

        :param func: The function which will be called when the menu item is
            selected.

        :param kwargs: Extra arguments to be passed to the constructor of
            :class:`earwax.MenuItem`.
        """
        menu_item: MenuItem = MenuItem(func, **kwargs)
        self.items.append(menu_item)
        return menu_item

    def make_sound(self, item: MenuItem, path: Path) -> Sound:
        """Return a sound object.

        :param item: The menu item to make the sound form.

            This value is probably :attr:`~earwax.Menu.current_item`.

        :param path: The path to load the sound from.

            This value will have been determined by
            :meth:`~earwax.Menu.show_selection`, and may have been loaded from
            the menu item itself, or the main earwax configuration.
        """
        return self.game.interface_sound_manager.play_path(
            path, False, looping=item.loop_select_sound
        )

    def show_selection(self) -> None:
        """Speak the menu item at the current position.

        If :attr:`self.position <earwax.Menu.position>` is -1, this method
        speaks :attr:`self.title <earwax.level.TitleMixin.title>`.

        This function performs no error checking, so it will happily throw
        errors if :attr:`position` is something stupid.
        """
        item: Optional[MenuItem] = self.current_item
        if self.select_sound is not None:
            self.select_sound.destroy()
            self.select_sound = None
        if item is None:
            self.game.output(self.title)
        else:
            if item.title is not None:
                self.game.output(item.title)
            item.dispatch_event('on_selected')
            sound_path: Optional[Path] = (
                item.select_sound_path
                or self.item_select_sound_path
                or self.game.config.menus.default_item_select_sound.value
            )
            if (
                sound_path is not None
                and self.game.interface_sound_manager is not None
            ):
                self.select_sound = self.make_sound(item, sound_path)

    def move_up(self) -> None:
        """Move up in this menu.

        Usually triggered by the up arrow key.
        """
        self.position = max(-1, self.position - 1)
        self.show_selection()

    def move_down(self) -> None:
        """Move down in this menu.

        Usually triggered by the down arrow key.
        """
        self.position = min(len(self.items) - 1, self.position + 1)
        self.show_selection()

    def activate(self) -> OptionalGenerator:
        """Activate the currently focused menu item.

        Usually triggered by the enter key.
        """
        item: Optional[MenuItem] = self.current_item
        if item is not None:
            sound_path: Optional[Path] = (
                item.activate_sound_path or
                self.item_activate_sound_path or
                self.game.config.menus.default_item_activate_sound.value
            )
            if (
                sound_path is not None and
                self.game.interface_sound_manager is not None
            ):
                self.game.interface_sound_manager.play_path(sound_path, True)
            res: OptionalGenerator = item.func()
            if res is not None and isgenerator(res):
                yield from res
            else:
                return res
        return None

    def home(self) -> None:
        """Move to the start of a menu.

        Usually triggered by the home key.
        """
        self.position = 0
        self.show_selection()

    def end(self) -> None:
        """Move to the end of a menu.

        Usually triggered by the end key.
        """
        self.position = len(self.items) - 1
        self.show_selection()

    def on_text(self, text: str) -> None:
        """Handle sent text.

        By default, performs a search of this menu.

        :param text: The text that has been sent.
        """
        now: float = time()
        if (now - self.search_time) > self.search_timeout:
            self.search_string = text.lower()
        else:
            self.search_string += text.lower()
        self.search_time = now
        index: int
        item: MenuItem
        for index, item in enumerate(self.items):
            if item.title is not None and item.title.lower().startswith(
                self.search_string
            ):
                self.position = index
                self.show_selection()
                break

    def on_push(self) -> None:
        """Handle this menu being pushed.

        This method is called when this object has been pushed onto a
        :class:`~earwax.game.Game` instance.

        By default, show the current selection. That will be the same as
        speaking the title, unless :attr:`self.position <earwax.Menu.position>`
        has been set to something other than -1..
        """
        self.show_selection()
        return super().on_push()

    def on_pop(self) -> None:
        """Destroy :attr:`~earwax.Menu.select_sound` if necessary."""
        if self.select_sound is not None:
            self.select_sound.destroy()
        return super().on_pop()

    def add_submenu(self, menu: 'Menu', replace: bool, **kwargs) -> MenuItem:
        """Add a submenu to this menu.

        :param menu: The menu to show when the resulting item is activated.

        :param replace: If ``True``, then the new menu will replace this one in
            the levels stack.

        :param kwargs: The additional arguments to pass to
            :meth:`~earwax.Menu.add_item`.
        """

        def inner() -> Generator[None, None, None]:
            """Push the menu."""
            yield
            if replace:
                self.game.replace_level(menu)
            else:
                self.game.push_level(menu)
            return None

        return self.item(**kwargs)(inner)
