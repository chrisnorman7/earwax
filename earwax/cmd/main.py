"""The Earwax command line utility.

This module provides the ``cmd_main`` function, and all sub commands.

To run the client:

* Make sure Earwax and all its dependencies are up to date.

* In the folder where you wish to work, type ``earwax``. This is a standard
    command line utility, which should provide enough of its own help that no
    replication is required in this document.

*NOTE*: At the time of writing, only the ``earwax story`` command actually does
all that much that is useful. Everything else needs fleshing out.

If you want to create more subcommands, add them in the subcommands directory,
then register them with the :meth:`subcommand` method.
"""

from argparse import (ArgumentDefaultsHelpFormatter, ArgumentParser, FileType,
                      Namespace, _SubParsersAction)
from logging import _nameToLevel, basicConfig
from typing import Callable

from .subcommands.configure_earwax import configure_earwax
from .subcommands.game import new_game
from .subcommands.init_project import init_project
from .subcommands.story import (build_story, create_story, edit_story,
                                play_story)
from .subcommands.vault import compile_vault, new_vault

SubcommandFunction = Callable[[Namespace], None]

parser: ArgumentParser = ArgumentParser()

parser.add_argument(
    '-l', '--log-file', type=FileType('w'), default='-', help='The log file'
)

parser.add_argument(
    '-L', '--log-level', choices=list(_nameToLevel), default='INFO',
    help='The logging level'
)

commands = parser.add_subparsers(
    metavar='<command>', required=True, description='The subcommand to call.'
)


def subcommand(
    name: str, func: SubcommandFunction,
    subparser: _SubParsersAction = commands,
    **kwargs
) -> ArgumentParser:
    """Add a subcommand to the argument parser.

    :param name: The name of the new command.

    :param func: The function that will be called when this subcommand is used.

    :param subparser: The parser to add the sub command to.

    :param kwargs: Keyword arguments to be passed to ``commands.add_parser``.
    """
    parser = subparser.add_parser(name, **kwargs)
    parser.set_defaults(func=func)
    return parser


subcommand(
    'init', init_project, formatter_class=ArgumentDefaultsHelpFormatter,
    description='Initialise or update an Earwax project in the current '
    'directory.'
)


def cmd_help(subcommand: _SubParsersAction) -> Callable[[Namespace], None]:
    """Return a command function that will show all subcommands."""

    def inner(args: Namespace) -> None:
        """Show all the possible subcommands."""
        print('Subcommands:')
        name: str
        p: ArgumentParser
        for name, p in sorted(
            subcommand.choices.items(), key=lambda item: item[0]
        ):
            print(f'{name}: {p.description}')

    return inner


subcommand(
    'help', cmd_help(commands),
    description='Show a list of all possible subcommands.',
    formatter_class=ArgumentDefaultsHelpFormatter, aliases=['commands']
)

subcommand(
    'config', configure_earwax, formatter_class=ArgumentDefaultsHelpFormatter,
    description='Configure the earwax module for use in your project.'
)

story_parser: ArgumentParser = commands.add_parser(
    'story', description='Play, edit, or build stories.'
)

story_subcommands: _SubParsersAction = story_parser.add_subparsers(
    metavar='<action>', required=True, help='The action to perform'
)

subcommand(
    'help', cmd_help(story_subcommands), subparser=story_subcommands,
    description='Show a list of all possible subcommands.',
    formatter_class=ArgumentDefaultsHelpFormatter, aliases=['commands']
)

play_story_parser: ArgumentParser = subcommand(
    'play', play_story, subparser=story_subcommands,
    formatter_class=ArgumentDefaultsHelpFormatter,
    description='Play a story file.'
)

play_story_parser.add_argument('filename', help='The filename to load from')

create_story_parser: ArgumentParser = subcommand(
    'new', create_story, subparser=story_subcommands,
    formatter_class=ArgumentDefaultsHelpFormatter,
    description='Create a new story file.'
)

create_story_parser.add_argument('filename', help='The filename to create')

edit_story_parser: ArgumentParser = subcommand(
    'edit', edit_story, subparser=story_subcommands,
    formatter_class=ArgumentDefaultsHelpFormatter,
    description='Edit a story file.'
)

edit_story_parser.add_argument('filename', help='The filename to load from')

build_story_parser: ArgumentParser = subcommand(
    'build', build_story, subparser=story_subcommands,
    formatter_class=ArgumentDefaultsHelpFormatter,
    description='Build a story file into a Python script.'
)

build_story_parser.add_argument(
    'world_filename', metavar='<worldfile>',
    help='The world file to load from'
)

build_story_parser.add_argument(
    'python_filename', metavar='<pythonfile>',
    help='The python file to write to'
)

build_story_parser.add_argument(
    '-s', '--sounds-directory', metavar='<directory>', default=None,
    help='The directory to copy sounds to'
)

game_parser: ArgumentParser = subcommand(
    'game', new_game, formatter_class=ArgumentDefaultsHelpFormatter,
    description='Create a blank game to work from.'
)

game_parser.add_argument('filename', help='The file to write the new game to')

vault_parser: ArgumentParser = commands.add_parser(
    'vault', description='Create or compile vault files.'
)

vault_subcommands: _SubParsersAction = vault_parser.add_subparsers(
    metavar='<action>', required=True, help='The action to perform'
)

subcommand(
    'help', cmd_help(vault_subcommands), subparser=vault_subcommands,
    description='Show a list of all possible subcommands.',
    formatter_class=ArgumentDefaultsHelpFormatter, aliases=['commands']
)

new_vault_parser: ArgumentParser = subcommand(
    'new', new_vault, subparser=vault_subcommands,
    formatter_class=ArgumentDefaultsHelpFormatter,
    description='Create a new vault file.'
)

new_vault_parser.add_argument(
    'filename', help='The name for the new vault file'
)

compile_vault_parser: ArgumentParser = subcommand(
    'compile', compile_vault, subparser=vault_subcommands,
    formatter_class=ArgumentDefaultsHelpFormatter,
    description='Compile an existing vault file.'
)

compile_vault_parser.add_argument(
    'filename', metavar='<vault-file>',
    help='The name of the vault file to compile'
)

compile_vault_parser.add_argument(
    'data_file', metavar='<data-file>',
    help='The name of the data file to create.', nargs='?', default=None
)


def cmd_main() -> None:
    """Run the earwax client."""
    args = parser.parse_args()
    basicConfig(stream=args.log_file, level=args.log_level)
    return args.func(args)
