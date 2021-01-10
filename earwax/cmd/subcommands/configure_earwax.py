"""Provides the configure_earwax subcommand."""

from argparse import Namespace
from pathlib import Path

try:
    from pyglet.window import Window
except ModuleNotFoundError:
    Window = object

from ... import ConfigMenu, Game
from ..constants import options_path


def configure_earwax(args: Namespace) -> None:
    """Configure earwax, using a :class:`earwax.ConfigMenu` instance."""
    path: Path = options_path
    if not path.is_file():
        print('Error: No options file found.')
        print()
        print('Please use the `init` subcommand first.')
        raise SystemExit
    window: Window = Window(caption='Configure Earwax')
    game: Game = Game()
    with path.open('r') as f:
        game.config.load(f)
    menu: ConfigMenu = ConfigMenu(  # type: ignore[misc]
        game, 'Configure Earwax', dismissible=False  # type: ignore[arg-type]
    )

    @menu.item(title='Save and Exit')
    def save_and_exit() -> None:
        """Save the configuration before exiting."""
        with path.open('w') as f:
            game.config.save(f)
        game.stop()

    @menu.item(title='Exit Without Saving')
    def exit_without_saving() -> None:
        """Exit without saving the configuration."""
        game.stop()

    game.run(window, initial_level=menu)
