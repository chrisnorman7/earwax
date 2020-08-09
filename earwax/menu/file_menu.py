"""Provides the FileMenu class."""

from pathlib import Path
from typing import Callable, Optional

from attr import attrs

from ..level import OptionalGenerator
from .menu import Menu


class _FileMenuBase:
    """The base class for the FileMenu class."""

    # The path the menu should start at.
    path: Path

    # The function which should be called when the user makes a selection.
    func: Callable[[Path], OptionalGenerator]

    # The root directory this menu is chrooted to.
    root: Optional[Path] = None

    # The label to be used when selecting null.
    #
    # If this value is None, it will not be possible to set the item to None.
    empty_label: Optional[str] = None

    # The label for selecting a directory.
    #
    # If this value is None, it will only be possible to select files.
    directory_label: Optional[str] = None

    # Selects whether or not to show directories.
    show_directories: bool = True

    # Selects whether or not to show files.
    show_files: bool = True

    # The label to be used for accessing the parent directory.
    #
    # If this value is None, it will not be possible to access the parent
    # directory.
    up_label: str = '..'


@attrs(auto_attribs=True)
class FileMenu(_FileMenuBase, Menu):
    """A menu for slecting a file."""

    def __attrs_post_init__(self):
        """Add the menu items."""
        if self.empty_label is not None:
            self.add_item(self.empty_label, lambda: self.func(None))
        if self.directory_label is not None:
            self.add_item(self.directory_label, lambda: self.func(self.path))
        if self.path != self.root:
            self.add_item(
                self.up_label, lambda: self.navigate_to(self.path.parent)
            )
        for child in self.path.iterdir():
            if child.is_file() and self.show_files:
                self.add_item(child.name, lambda p=child: self.func(p))
            elif child.is_dir() and self.show_directories:
                self.add_item(child.name, lambda p=child: self.navigate_to(p))

    def navigate_to(self, path: Path) -> None:
        """Navigate to a different path. Instead of completely replacing the
        menu, just change the path, and re-use this instance."""
        self.path = path
        self.home()
