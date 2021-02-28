"""Provides the init_project subcommand."""

from argparse import Namespace
from pathlib import Path

from ...configuration import EarwaxConfig
from ..constants import (
    maps_directory,
    options_path,
    project_filename,
    scripts_directory,
)
from ..project import Project


def update() -> None:
    """Update the given path to conform to the latest earwax file structure.

    :param p: The path to update.
    """
    if not options_path.is_file():
        print("Saving earwax configuration.")
        config: EarwaxConfig = EarwaxConfig()
        with options_path.open("w") as f:
            config.save(f)
    else:
        print("Earwax configuration already exists.")
    path: Path
    cwd: Path = Path.cwd()
    for path in (maps_directory, scripts_directory):
        if not path.is_dir():
            path.mkdir()
            print(f"Created directory {path.relative_to(cwd)}.")
        else:
            print(f"Skipping directory {path.relative_to(cwd)}.")


def init_project(args: Namespace) -> None:
    """Initialise or update the project at the given directory."""
    cwd: Path = Path.cwd()
    if project_filename.is_file():
        print(
            "There is already a project file at "
            f"{project_filename.relative_to(cwd)}."
        )
    else:
        project: Project = Project(name="Untitled Project")
        project.save(project_filename)
        print(
            f"Created {project.name} at {project_filename.relative_to(cwd)}."
        )
    update()
    print("Updated.")
