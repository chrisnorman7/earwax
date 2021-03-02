"""Provides subcommands for working with maps."""

from argparse import Namespace
from pathlib import Path

from earwax import Game, MapEditor
from pyglet.window import Window

from ...mapping.map_editor import LevelMap


def new_map(args: Namespace) -> None:
    """Create a new map."""
    p: Path = Path(args.filename)
    if p.exists():
        print("Error:")
        print()
        print(f"Path already exists: {args.filename}.")
        raise SystemExit
    level_map: LevelMap = LevelMap()
    level_map.save(p)
    print(f"Map created at {args.filename}.")


def edit_map(args: Namespace) -> None:
    """Edit the map at the given filename."""
    p: Path = args.filename
    if not p.is_file():
        print("Error:")
        print()
        print(f"Path does not exist: {p}.")
        raise SystemExit
    game: Game = Game(name="Map Editor")
    level: MapEditor = MapEditor(game, filename=p)
    window: Window = Window(caption=game.name)
    game.run(window, initial_level=level)
