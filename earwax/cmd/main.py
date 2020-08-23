"""Provides the main function."""

from pyglet.window import Window

from .constants import game
from .menu import main_menu


def cmd_main() -> None:
    """The main entry point.

    This function will be called by the earwax script."""
    window: Window = Window(caption='Earwax')
    game.push_level(main_menu)
    game.run(window)
