"""Provides commands for working with call response trees."""

from argparse import Namespace
from pathlib import Path

from pyglet.window import Window

from ...call_response_level import CallResponseEditor, CallResponseTree
from ...game import Game


def new_crt(args: Namespace) -> None:
    """Create a new call response tree."""
    t: CallResponseTree = CallResponseTree()
    filename: Path = Path(args.filename)
    if filename.exists():
        print("Error:")
        print()
        print(
            f"Cannot create a new call response tree at {filename}: "
            "File already exists."
        )
    else:
        t.save(filename)
        print(f"Created a new call response tree at {filename}.")


def edit_crt(args: Namespace) -> None:
    """Edit a call response tree."""
    filename: Path = Path(args.filename)
    if not filename.is_file():
        print("Error:")
        print()
        print(f"File does not exist: {filename}.")
    else:
        t: CallResponseTree = CallResponseTree.from_filename(filename)
        game: Game = Game()
        window: Window = Window(
            caption=f"Edit Call Response Tree - {filename}"
        )
        editor: CallResponseEditor = CallResponseEditor(
            game, tree=t, filename=filename
        )
        game.run(window, initial_level=editor)
