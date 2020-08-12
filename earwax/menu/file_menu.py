"""Provides the FileMenu class."""

from pathlib import Path
from typing import Callable, Optional

from attr import attrs

from ..action import OptionalGenerator
from .menu import Menu


@attrs(auto_attribs=True)
class FileMenuBase:
    """Adds path and func arguments."""

    # The path this menu will start at.
    path: Path

    # The function to run with the resulting file or directory.
    func: Callable[[Optional[Path]], OptionalGenerator]


@attrs(auto_attribs=True)
class FileMenu(FileMenuBase, Menu):
    """A menu for slecting a file."""

    # The root directory which this menu will be chrooted to.
    root: Optional[Path] = None

    # The label given to an entry which will allow this menu to return None as
    # a result.
    #
    # If this label is None (the default), then then no such option will be
    # available.
    empty_label: Optional[str] = None

    # The label given to an entry which will allow a directory - in addition to
    # files - to be selected.
    #
    # If this argument is None (the default), then no such option will be
    # available.
    #
    # If you only want directories to be selected, then pass show_files=False
    # to the constructor.
    directory_label: Optional[str] = None

    # Whether or not to show directories in the list.
    show_directories: bool = True

    # Whether or not to include files in the list.
    show_files: bool = True

    # The label given to the entry to go up in the directory tree.
    up_label: str = '..'

    def __attrs_post_init__(self) -> None:
        """Add the menu items."""
        super().__attrs_post_init__()
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
