"""Provides the game_title subcommand."""

from ..workspace import Workspace
from argparse import Namespace


def game_title(args: Namespace) -> None:
    """Rename the current workspace."""
    try:
        workspace = Workspace.load()
        workspace.title = args.title
        workspace.save()
        print(f'Game renamed to {workspace.title}.')
    except FileNotFoundError:
        print('Error: No game has been created yet.')
        print()
        print('Try using the `init` subcommand first.')
