"""Provides the game_surfaces subcommand."""

from argparse import Namespace
from pathlib import Path

from ..constants import surfaces_directory


def game_surfaces(args: Namespace) -> None:
    """Shows a list of surfaces.

    Optionally shows what files are in a given directory."""
    surface: Path
    if args.surface is None:
        print('Surfaces:')
        for surface in surfaces_directory.iterdir():
            print(surface.name)
    else:
        surface = surfaces_directory / args.surface
        surface = surface.absolute()
        if surface.is_dir():
            print(f'Showing files in {surface.relative_to(Path.cwd())}:')
            surface_file: Path
            for surface_file in surface.iterdir():
                print(surface_file.name)
        else:
            print(f'Error: There is no surface named {args.surface}.')
            print()
            print(
                f'To add a surface, create THE {surface} directory, and put '
                'your sound files in it.'
            )
