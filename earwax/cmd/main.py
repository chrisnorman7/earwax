"""Provides the main function, and registers subcommands.

If you want to create more subcommands, add them in the subcommands directory,
then register them with the :meth:`subcommand` method.
"""

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from typing import Callable

from .constants import surfaces_directory
from .subcommands.build_surfaces import build_surfaces
from .subcommands.configure_earwax import configure_earwax
from .subcommands.init_project import init_project
from .subcommands.project_surfaces import project_surfaces
from .subcommands.project_title import project_title

SubcommandFunction = Callable[[Namespace], None]

parser: ArgumentParser = ArgumentParser(
    formatter_class=ArgumentDefaultsHelpFormatter
)

commands = parser.add_subparsers(
    metavar='<command>', required=True, description='The subcommand to call.'
)


def subcommand(
    name: str, func: SubcommandFunction, **kwargs
) -> ArgumentParser:
    """Add a subcommand to the argument parser.

    :param name: The name of the new command.

    :param func: The function that will be called when this subcommand is used.

    :param kwargs: Keyword arguments to be passed to ``commands.add_parser``.
    """
    parser = commands.add_parser(name, **kwargs)
    parser.set_defaults(func=func)
    return parser


subcommand(
    'init', init_project, formatter_class=ArgumentDefaultsHelpFormatter,
    description='Initialise or update an Earwax project in the current '
    'directory.'
)


def cmd_help(args: Namespace) -> None:
    """Shows all the possible subcommands."""
    print('Subcommands:')
    name: str
    parser: ArgumentParser
    for name, parser in sorted(
        commands.choices.items(), key=lambda item: item[0]
    ):
        print(f'{name}: {parser.description}')


subcommand(
    'help', cmd_help, description='Show a list of all possible subcommands.',
    formatter_class=ArgumentDefaultsHelpFormatter, aliases=['commands']
)

subcommand(
    'config', configure_earwax, formatter_class=ArgumentDefaultsHelpFormatter,
    description='Configure the earwax module for use in your project.'
)

project_surfaces_parser = subcommand(
    'surfaces', project_surfaces,
    formatter_class=ArgumentDefaultsHelpFormatter,
    description=f'Show the surfaces from the {surfaces_directory} directory.'
)

project_surfaces_parser.add_argument(
    'surface', default=None, help='The name of a surface to view files for',
    nargs='?'
)

project_title_parser = subcommand(
    'title', project_title, formatter_class=ArgumentDefaultsHelpFormatter,
    description='Rename the current project.'
)

project_title_parser.add_argument('title', help='The new name')

subcommand(
    'build-surfaces', build_surfaces,
    formatter_class=ArgumentDefaultsHelpFormatter,
    description='Build a python file containing all the current surfaces.'
)


def cmd_main() -> None:
    args = parser.parse_args()
    return args.func(args)
