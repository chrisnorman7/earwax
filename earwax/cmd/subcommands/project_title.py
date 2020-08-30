"""Provides the project_title subcommand."""

from argparse import Namespace

from ..project import Project


def project_title(args: Namespace) -> None:
    """Rename the current workspace."""
    try:
        project = Project.load()
        project.title = args.title
        project.save()
        print(f'Project renamed to {project.title}.')
    except FileNotFoundError:
        print('Error: No project has been created yet.')
        print()
        print('Try using the `init` subcommand first.')
