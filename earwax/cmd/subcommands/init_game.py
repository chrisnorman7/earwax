"""Provides the update_game subcommand."""

from argparse import Namespace
from pathlib import Path

from ... import EarwaxConfig
from ..constants import (ambiances_directory, levels_directory,
                         music_directory, options_file, sounds_directory,
                         surfaces_directory, workspace_file)
from ..workspace import Workspace


def update(p: Path) -> None:
    """Update the given path to conform to the latest earwax file structure.

    :param p: The path to update.
    """
    options_path: Path = p / options_file
    if not options_path.is_file():
        print('Saving earwax configuration.')
        config: EarwaxConfig = EarwaxConfig()
        with options_path.open('w') as f:
            config.save(f)
    else:
        print('Earwax configuration already exists.')
    path: Path
    for path in (
        sounds_directory, surfaces_directory, ambiances_directory,
        music_directory, levels_directory
    ):
        path = p / path
        if not path.is_dir():
            path.mkdir()
            print(f'Created directory {path.relative_to(p)}.')
        else:
            print(f'Skipping directory {path.relative_to(p)}.')


def init_game(args: Namespace) -> None:
    """Update the game at the given directory."""
    directory: Path = Path.cwd()
    workspace_path: Path = directory / workspace_file
    if workspace_path.is_file():
        print(f'There is already a game file at {workspace_path}.')
    else:
        workspace: Workspace = Workspace(title='Untitled Game')
        workspace.save()
        print(f'Created {workspace.title}.')
    update(directory)
    print('Updated.')
