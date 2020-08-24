"""Provides the main_menu object."""

from earwax import Menu

from ..constants import game


class MainMenu(Menu):
    """The main menu for the earwax program."""

    def __init__(self) -> None:
        super().__init__('Main Menu', game)
        self.item('New Game')(self.new_game)
        self.item('Exit')(self.do_exit)

    def new_game(self) -> None:
        """Create a new game."""
        print('New game.')
        game.pop_level()

    def do_exit(self) -> None:
        """Exit the program."""
        if game.window is not None:
            game.window.close()
