"""Provides the main_menu object."""

from earwax import Menu

from ..constants import game

main_menu = Menu('Main Menu', game, dismissible=False)


@main_menu.item('New Game')
def new_game() -> None:
    """Create a new game."""
    print('New game.')
    game.pop_level()


@main_menu.item('Exit')
def do_exit() -> None:
    """Exit the program."""
    if game.window is not None:
        game.window.close()
