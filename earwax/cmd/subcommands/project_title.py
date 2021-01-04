"""Provides the project_title subcommand."""

from argparse import Namespace

from ..project import Project


def project_title(args: Namespace) -> None:
    """Rename the current workspace."""
    try:
        project: Project = Project.from_file()
        if args.title is None:
            print(f'Project title: {project.name}.')
        else:
            project.name = args.title
            project.save()
            print(f'Project renamed to {project.name}.')
    except FileNotFoundError:
        print('Error: No project has been created yet.')
        print()
        print('Try using the `init` subcommand first.')
