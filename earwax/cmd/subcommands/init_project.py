"""Provides the init_project subcommand."""

from argparse import Namespace
from pathlib import Path

from ... import EarwaxConfig
from ..constants import (ambiances_directory, levels_directory,
                         music_directory, options_filename, project_filename,
                         sounds_directory, surfaces_directory)
from ..project import Project


def update(p: Path) -> None:
    """Update the given path to conform to the latest earwax file structure.

    :param p: The path to update.
    """
    options_path: Path = p / options_filename
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


def init_project(args: Namespace) -> None:
    """Initialise or update the project at the given directory."""
    directory: Path = Path.cwd()
    project_path: Path = directory / project_filename
    if project_path.is_file():
        print(f'There is already a project file at {project_path}.')
    else:
        project: Project = Project(title='Untitled Game')
        project.save()
        print(f'Created {project.title}.')
    update(directory)
    print('Updated.')
