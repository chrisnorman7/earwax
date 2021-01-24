"""Provides the game subcommand."""

import os.path
from argparse import Namespace
from inspect import getsource


def new_game(args: Namespace) -> None:
    """Create a default game."""
    if os.path.exists(args.filename):
        print(f'Error: File already exists: {args.filename}.')
    else:
        print(f'Creating a blank game at {args.filename}.')
        from .. import blank_game
        with open(args.filename, 'w') as f:
            code: str = getsource(blank_game)
            f.write(code)
        print('Done.')
