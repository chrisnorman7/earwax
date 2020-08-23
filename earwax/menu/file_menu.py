"""Provides the FileMenu class."""

from pathlib import Path
from typing import Callable, Optional

from attr import attrs

from ..action import OptionalGenerator
from .menu import Menu


@attrs(auto_attribs=True)
class FileMenuBase:
    """Adds path and func arguments."""

    path: Path
    func: Callable[[Optional[Path]], OptionalGenerator]


@attrs(auto_attribs=True)
class FileMenu(FileMenuBase, Menu):
    """A menu for slecting a file.

        >>> from pathlib import Path
        >>> from earwax import Game, Level, FileMenu, tts
        >>> from pyglet.window import key, Window
        >>> w = Window(caption='Test Game')
        >>> g = Game()
        >>> l = Level()
        >>> @l.action('Show file menu', symbol=key.F)
        ... def file_menu():
        ...     '''Show a file menu.'''
        ...     def inner(p):
        ...         tts.speak(str(p))
        ...         g.pop_level()
        ...     f = FileMenu(Path.cwd(), inner, 'File Menu', g)
        ...     g.push_level(f)
        ...
        >>> g.push_level(l)
        >>> g.run(w)

    :ivar ~file_menu.FileMenuBase.path: The path this menu will start at.

    :ivar ~file_menu.FileMenuBase.func: The function to run with the resulting
        file or directory.

    :ivar ~file_menu.FileMenu.root: The root directory which this menu will be
        chrooted to.

    :ivar ~file_menu.FileMenu.empty_label: The label given to an entry which
        will allow this menu to return None as a result.

        If this label is None (the default), then then no such option will be
        available.

    :ivar ~file_menu.FileMenu.directory_label: The label given to an entry
        which will allow a directory - in addition to files - to be selected.

        If this argument is None (the default), then no such option will be
        available.

        If you only want directories to be selected, then pass show_files=False
        to the constructor.

    :ivar ~file_menu.FileMenu.show_directories: Whether or not to show
        directories in the list.

    :ivar ~file_menu.FileMenu.show_files: Whether or not to include files in
        the list.

    :ivar ~file_menu.FileMenu.up_label: The label given to the entry to go up
        in the directory tree.
    """

    root: Optional[Path] = None
    empty_label: Optional[str] = None
    directory_label: Optional[str] = None
    show_directories: bool = True
    show_files: bool = True
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
        """Navigate to a different path.

        Instead of completely replacing the menu, just change the path, and re-
        use this instance."""

        def inner() -> None:
            self.path = path
            self.home()

        return inner

    def select_item(self, path: Optional[Path]) -> Callable[
        [], OptionalGenerator
    ]:
        """Used as the menu handler in place of a lambda."""

        def inner():
            return self.func(path)

        return inner
