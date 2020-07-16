"""Provides menu-related classes."""

import os
import os.path

from attr import Factory, attrib, attrs

from .speech import tts

NoneType = type(None)


@attrs
class MenuItem:
    """An item in a menu."""

    # The title of this menu item.
    title = attrib()

    # The function which will be called when this item is activated.
    func = attrib()

    # The function which will be called when this item is selected.
    on_selected = attrib(default=Factory(NoneType))


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

    def add_item(self, title, func, **kwargs):
        """Add an item to this menu. All arguments are passed to the
        constructor of MenuItem."""
        mi = MenuItem(title, func, **kwargs)
        self.items.append(mi)
        return mi

    def show_selection(self):
        """Speak the menu item at the current position, or the title of this
        menu, if position is -1.

        This function performs no error checking, so it will happily throw
        errors if self.position is something stupid."""
        if self.position == -1:
            tts.speak(self.title)
        else:
            item = self.current_item
            tts.speak(item.title)
            if item.on_selected is not None:
                item.on_selected()

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
            return self.current_item.func()


class FileMenu(Menu):
    """A menu for slecting a file."""
    def __init__(
        self, game, title, path, func, *, root=None, empty_label=None,
        directory_label=None, on_directory_item=None, on_file_item=None,
        on_selected=None, show_directories=True, show_files=True, up_label='..'
    ):
        """Add menu items."""
        super().__init__(title)
        if empty_label is not None:
            self.add_item(empty_label, lambda: func(None))
        if directory_label is not None:
            self.add_item(
                directory_label, lambda p=path: func(p)
            )
        if path != root:
            self.add_item(
                up_label, lambda: game.replace_menu(
                    FileMenu(
                        game, title, os.path.dirname(path), func, root=root,
                        empty_label=empty_label,
                        directory_label=directory_label,
                        on_directory_item=on_directory_item,
                        on_file_item=on_file_item, on_selected=on_selected,
                        show_directories=show_directories,
                        show_files=show_files, up_label=up_label
                    )
                )
            )
        for name in os.listdir(path):
            full_path = os.path.join(path, name)
            if os.path.isfile(full_path) and show_files:
                item = self.add_item(
                    name, lambda p=full_path: func(p),
                    on_selected=lambda p=full_path: on_selected(p)
                )
                if on_file_item is not None:
                    on_file_item(full_path, item)
            elif os.path.isdir(full_path) and show_directories:
                item = self.add_item(
                    name, lambda p=full_path: game.replace_menu(
                        FileMenu(
                            game, title, p, func, root=root,
                            empty_label=empty_label,
                            directory_label=directory_label,
                            on_directory_item=on_directory_item,
                            on_file_item=on_file_item, on_selected=on_selected,
                            show_directories=show_directories,
                            show_files=show_files, up_label=up_label
                        )
                    ), on_selected=lambda p=full_path: on_selected(p)
                )
                if on_directory_item is not None:
                    on_directory_item(full_path, item)


class ActionMenu(Menu):
    """A menu to show a list of actions, and their associated triggers."""
    def __init__(self, game, on_selected=None):
        super().__init__('Actions')
        for a in game.actions:
            self.add_item(
                str(a), lambda action=a: self.handle_action(game, action),
                on_selected=on_selected
            )

    def handle_action(self, game, action):
        """Handle an action."""
        game.clear_menus()
        action.run(None)
