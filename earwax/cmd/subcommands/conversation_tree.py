"""Provides commands for working with call response trees."""

from argparse import Namespace
from pathlib import Path

from pyglet.window import Window

from ...conversation_level import ConversationEditor, ConversationTree
from ...game import Game


def new_convo(args: Namespace) -> None:
    """Create a new conversation tree."""
    t: ConversationTree = ConversationTree()
    filename: Path = Path(args.filename)
    if filename.exists():
        print("Error:")
        print()
        print(
            f"Cannot create a new conversation tree at {filename}: "
            "ile already exists."
        )
    else:
        t.save(filename)
        print(f"Created a new conversation tree at {filename}.")


def edit_convo(args: Namespace) -> None:
    """Edit a conversation tree."""
    filename: Path = Path(args.filename)
    if not filename.is_file():
        print("Error:")
        print()
        print(f"File does not exist: {filename}.")
    else:
        t: ConversationTree = ConversationTree.from_filename(filename)
        game: Game = Game()
        window: Window = Window(caption=f"Conversation Tree - {filename}")
        editor: ConversationEditor = ConversationEditor(
            game, tree=t, filename=filename
        )
        game.run(window, initial_level=editor)
