"""Provides menu-related classes."""

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Generator, List, Optional

from attr import Factory, attrib, attrs

if TYPE_CHECKING:
    from .action import ActionFunctionType
    from .game import Game

from .speech import tts

OptionalGenerator = Optional[Generator[None, None, None]]


@attrs(auto_attribs=True)
class MenuItem:
    """An item in a menu."""

    # The title of this menu item.
    title: str

    # The function which will be called when this item is activated.
    func: 'ActionFunctionType'

    # The function which will be called when this item is selected.
    on_selected: Optional[Callable[[], None]] = Factory(lambda: None)


@attrs(auto_attribs=True)
class Menu:
    """A menu which holds multiple menu items which can be activated using
    actions."""

    # The title of this menu.
    title: str

    # Whether or not it should be possible to dismiss this menu.
    dismissible: bool = Factory(lambda: True)

    # The player's position in this menu.
    position: int = Factory(lambda: -1)

    # The list of MenuItem instances for this menu.
    items: List[MenuItem] = attrib(default=Factory(list), init=False)

    @property
    def current_item(self) -> Optional[MenuItem]:
        """Return the currently selected menu item. If position is -1, return
        None."""
        if self.position != -1:
            return self.items[self.position]
        return None

    def add_item(
        self, title: str, func: 'ActionFunctionType', **kwargs
    ) -> MenuItem:
        """Add an item to this menu. All arguments are passed to the
        constructor of MenuItem."""
        mi: MenuItem = MenuItem(title, func, **kwargs)
        self.items.append(mi)
        return mi

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
            if item.on_selected is not None:
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


class FileMenu(Menu):
    """A menu for slecting a file."""
    def __init__(
        self, game: 'Game', title: str, path: Path,
        func: Callable[[Optional[Path]], OptionalGenerator], *,
        root: Path = None, empty_label: str = None,
        directory_label: str = None, on_directory_item: Callable[
            [Path, MenuItem], None
        ] = None, on_file_item: Callable[[Path, MenuItem], None] = None,
        on_selected: Callable[[Path], None] = None,
        show_directories: bool = True, show_files: bool = True,
        up_label: str = '..'
    ):
        """Add menu items."""
        super().__init__(title)
        if empty_label is not None:
            self.add_item(empty_label, lambda: func(None))
        if directory_label is not None:

            def use_current_directory(p: Path = path) -> Optional[
                Generator[None, None, None]
            ]:
                return func(p)

            self.add_item(directory_label, use_current_directory)
        if path != root:
            self.add_item(
                up_label, lambda: game.replace_menu(
                    FileMenu(
                        game, title, path.parent, func, root=root,
                        empty_label=empty_label,
                        directory_label=directory_label,
                        on_directory_item=on_directory_item,
                        on_file_item=on_file_item, on_selected=on_selected,
                        show_directories=show_directories,
                        show_files=show_files, up_label=up_label
                    )
                )
            )
        for child in path.iterdir():
            def _on_selected(p: Path = child) -> None:
                if on_selected is not None:
                    on_selected(p)

            if child.is_file() and show_files:

                def select_file(p: Path = child) -> OptionalGenerator:
                    return func(p)

                item = self.add_item(
                    child.name, select_file, on_selected=_on_selected
                )
                if on_file_item is not None:
                    on_file_item(child, item)
            elif child.is_dir() and show_directories:

                def select_directory(p: Path = child) -> None:
                    game.replace_menu(
                        FileMenu(
                            game, title, p, func, root=root,
                            empty_label=empty_label,
                            directory_label=directory_label,
                            on_directory_item=on_directory_item,
                            on_file_item=on_file_item, on_selected=on_selected,
                            show_directories=show_directories,
                            show_files=show_files, up_label=up_label
                        )
                    )

                item = self.add_item(
                    child.name, select_directory, on_selected=_on_selected
                )
                if on_directory_item is not None:
                    on_directory_item(child, item)


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
