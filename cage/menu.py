"""Provides menu-related classes."""

import os
import os.path

from attr import Factory, attrib, attrs

from .speech import tts


@attrs
class MenuItem:
    """An item in a menu."""

    title = attrib()
    func = attrib()


@attrs
class Menu:
    """A menu which holds multiple menu items which can be activated using
    actions."""

    # The title of this menu.
    title = attrib()

    # Whether or not it should be possible to dismiss this menu.
    dismissible = attrib(default=Factory(lambda: True))

    # The player's position in this menu.
    position = attrib(default=Factory(lambda: -1))

    # The list of MenuItem instances for this menu.
    items = attrib(default=Factory(list), init=False)

    @property
    def current_item(self):
        """Return the currently selected menu item. If position is -1, return
        None."""
        if self.position != -1:
            return self.items[self.position]

    def add_item(self, title, func):
        """Add an item to this menu."""
        self.items.append(MenuItem(title, func))

    def show_selection(self):
        """Speak the menu item at the current position, or the title of this
        menu, if position is -1.

        This function performs no error checking, so it will happily throw
        errors if self.position is something stupid."""
        if self.position == -1:
            tts.speak(self.title)
        else:
            tts.speak(self.current_item.title)

    def move_up(self):
        """Move up in this menu."""
        self.position = max(-1, self.position - 1)
        self.show_selection()

    def move_down(self):
        """Move down in this menu."""
        self.position = min(len(self.items) - 1, self.position + 1)
        self.show_selection()

    def activate(self):
        """Activate the currently focused menu item."""
        if self.position != -1:
            self.current_item.func()


class FileMenu(Menu):
    """A menu for slecting a file."""
    def __init__(
        self, game, title, path, func, root=None, empty_ok=None,
        directory_ok=False
    ):
        """Add menu items."""
        super().__init__(title)
        if (empty_ok):
            self.add_item('Clear', lambda: func(None))
        if directory_ok:
            self.add_item(
                'Use Directory', lambda p=path: func(p)
            )
        if path != root:
            self.add_item(
                '..', lambda: game.replace_menu(
                    FileMenu(
                        game, title, os.path.dirname(path), func, root,
                        empty_ok, directory_ok
                    )
                )
            )
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            if os.path.isfile(full_path):
                self.add_item(name, lambda p=full_path: func(p))
            elif os.path.isdir(full_path):
                self.add_item(
                    name, lambda p=full_path: game.replace_menu(
                        FileMenu(
                            game, title, p, func, root=root, empty_ok=empty_ok,
                            directory_ok=directory_ok
                        )
                    )
                )
