"""Provides the main function."""

from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from typing import Callable

from .subcommands.configure_earwax import configure_earwax
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
    'config', configure_earwax, formatter_class=ArgumentDefaultsHelpFormatter
)


def cmd_main() -> None:
    args = parser.parse_args()
    return args.func(args)
