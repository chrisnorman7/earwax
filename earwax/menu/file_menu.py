"""Provides the FileMenu class."""

from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from ..game import Game

from ..level import OptionalGenerator
from .menu import Menu


class FileMenu(Menu):
    """A menu for slecting a file."""

    def __init__(
        self, game: 'Game', title: str, path: Path, func: Callable[
            [Optional[Path]], OptionalGenerator
        ], root: Optional[Path] = None, empty_label: Optional[str] = None,
        directory_label: Optional[str] = None, show_directories: bool = True,
        show_files: bool = True, up_label: str = '..', **kwargs
    ) -> None:
        """Add the menu items."""
        super().__init__(game, title, **kwargs)
        self.path = path
        self.func = func
        self.root = root
        self.empty_label = empty_label
        self.directory_label = directory_label
        self.show_directories = show_directories
        self.show_files = show_files
        self.up_label = up_label
        if self.empty_label is not None:
            self.add_item(self.empty_label, self.select_item(None))
        if self.directory_label is not None:
            self.add_item(self.directory_label, self.select_item(self.path))
        if self.path != self.root and self.up_label is not None:
            self.add_item(self.up_label, self.navigate_to(self.path.parent))
        for child in self.path.iterdir():
            if child.is_file() and self.show_files:
                self.add_item(child.name, self.select_item(child))
            elif child.is_dir() and self.show_directories:
                self.add_item(child.name, self.navigate_to(child))

    def navigate_to(self, path: Path) -> Callable[[], None]:
        """Navigate to a different path. Instead of completely replacing the
        menu, just change the path, and re-use this instance."""

        def inner() -> None:
            self.path = path
            self.home()

        return inner

    def select_item(self, path: Optional[Path]) -> Callable[
        [], OptionalGenerator
    ]:
        """Used in place of a lambda."""

        def inner():
            return self.func(path)

        return inner
