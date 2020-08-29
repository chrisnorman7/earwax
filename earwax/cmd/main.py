"""Provides the main function, and registers subcommands.

If you want to create more subcommands, add them in the subcommands directory,
then register them with the :meth:`subcommand` method.
"""

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from typing import Callable

from .constants import surfaces_directory
from .subcommands.configure_earwax import configure_earwax
from .subcommands.game_surfaces import game_surfaces
from .subcommands.init_game import init_game

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
    'init', init_game, formatter_class=ArgumentDefaultsHelpFormatter,
    description='Initialise or update an Earwax game in the current directory'
)


def cmd_help(args: Namespace) -> None:
    """Shows all the possible subcommands."""
    print('Subcommands:')
    name: str
    parser: ArgumentParser
    for name, parser in commands.choices.items():
        print(f'{name}: {parser.description}')


subcommand(
    'help', cmd_help, description='Show a list of all possible subcommands.',
    formatter_class=ArgumentDefaultsHelpFormatter
)

subcommand(
    'config', configure_earwax, formatter_class=ArgumentDefaultsHelpFormatter,
    description='Configure the earwax module for use in your game.'
)

game_surfaces_parser = subcommand(
    'surfaces', game_surfaces, formatter_class=ArgumentDefaultsHelpFormatter,
    description=f'Show the surfaces from the {surfaces_directory} directory.'
)

game_surfaces_parser.add_argument(
    'surface', default=None, help='The name of a surface to view files for',
    nargs='?'
)


def cmd_main() -> None:
    args = parser.parse_args()
    return args.func(args)
