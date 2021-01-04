"""Provides the init_project subcommand."""

from argparse import Namespace
from pathlib import Path

from ... import EarwaxConfig
from ..constants import (ambiances_directory, maps_directory, music_directory,
                         options_path, project_filename, scripts_directory,
                         sounds_directory, surfaces_directory)
from ..project import Project


def update() -> None:
    """Update the given path to conform to the latest earwax file structure.

    :param p: The path to update.
    """
    if not options_path.is_file():
        print('Saving earwax configuration.')
        config: EarwaxConfig = EarwaxConfig()
        with options_path.open('w') as f:
            config.save(f)
    else:
        print('Earwax configuration already exists.')
    path: Path
    cwd: Path = Path.cwd()
    for path in (
        sounds_directory, surfaces_directory, ambiances_directory,
        music_directory, maps_directory, scripts_directory
    ):
        if not path.is_dir():
            path.mkdir()
            print(f'Created directory {path.relative_to(cwd)}.')
        else:
            print(f'Skipping directory {path.relative_to(cwd)}.')


def init_project(args: Namespace) -> None:
    """Initialise or update the project at the given directory."""
    cwd: Path = Path.cwd()
    if project_filename.is_file():
        print(
            'There is already a project file at '
            f'{project_filename.relative_to(cwd)}.'
        )
    else:
        project: Project = Project(name='Untitled Project')
        project.save()
        print(f'Created {project.name}.')
    update()
    print('Updated.')
