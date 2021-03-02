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
                      HelpFormatter, Namespace, _SubParsersAction)
from logging import _nameToLevel, basicConfig
from pathlib import Path
from typing import Callable, Type

from .subcommands.call_response_tree import edit_crt, new_crt
from .subcommands.configure_earwax import configure_earwax
from .subcommands.game import new_game
from .subcommands.game_map import edit_map, new_map
from .subcommands.init_project import init_project
from .subcommands.story import (build_story, create_story, edit_story,
                                play_story)
from .subcommands.vault import compile_vault, new_vault

SubcommandFunction = Callable[[Namespace], None]


def subcommand(
    name: str,
    func: SubcommandFunction,
    subparser: _SubParsersAction,
    formatter_class: Type[HelpFormatter] = ArgumentDefaultsHelpFormatter,
    **kwargs,
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


def cmd_help(subcommand: _SubParsersAction) -> Callable[[Namespace], None]:
    """Return a command function that will show all subcommands."""

    def inner(args: Namespace) -> None:
        """Show all the possible subcommands."""
        print("Subcommands:")
        name: str
        p: ArgumentParser
        for name, p in sorted(
            subcommand.choices.items(), key=lambda item: item[0]
        ):
            print(f"{name}: {p.description}")

    return inner


def add_help(subparser: _SubParsersAction) -> ArgumentParser:
    """Add a help command to any subcommand."""
    return subcommand(
        "help",
        cmd_help(subparser),
        subparser,
        aliases=["commands"],
        description="Show a list of all possible subcommands.",
    )


parser: ArgumentParser = ArgumentParser()

parser.add_argument(
    "-l", "--log-file", type=FileType("w"), default="-", help="The log file"
)

parser.add_argument(
    "-L",
    "--log-level",
    choices=list(_nameToLevel),
    default="INFO",
    help="The logging level",
)


def add_subcommands(_parser: ArgumentParser) -> _SubParsersAction:
    """Add subcommands to any parser.

    :param _parser: The parser to add subcommands to.
    """
    subcommands: _SubParsersAction = _parser.add_subparsers(
        metavar="<action>", required=True, help="The action to perform"
    )
    add_help(subcommands)
    return subcommands


commands = add_subcommands(parser)


subcommand(
    "init",
    init_project,
    commands,
    description="Initialise or update an Earwax project in the current "
    "directory.",
)


subcommand(
    "config",
    configure_earwax,
    commands,
    description="Configure the earwax module for use in your project.",
)

story_parser: ArgumentParser = commands.add_parser(
    "story", description="Play, edit, or build stories."
)

story_subcommands: _SubParsersAction = add_subcommands(story_parser)

play_story_parser: ArgumentParser = subcommand(
    "play", play_story, story_subcommands, description="Play a story file."
)

play_story_parser.add_argument("filename", help="The filename to load from")

create_story_parser: ArgumentParser = subcommand(
    "new",
    create_story,
    story_subcommands,
    description="Create a new story file.",
)

create_story_parser.add_argument("filename", help="The filename to create")

edit_story_parser: ArgumentParser = subcommand(
    "edit", edit_story, story_subcommands, description="Edit a story file."
)

edit_story_parser.add_argument("filename", help="The filename to load from")

build_story_parser: ArgumentParser = subcommand(
    "build",
    build_story,
    story_subcommands,
    description="Build a story file into a Python script.",
)

build_story_parser.add_argument(
    "world_filename", metavar="<worldfile>", help="The world file to load from"
)

build_story_parser.add_argument(
    "python_filename",
    metavar="<pythonfile>",
    help="The python file to write to",
)

build_story_parser.add_argument(
    "-s",
    "--sounds-directory",
    metavar="<directory>",
    default=None,
    help="The directory to copy sounds to",
)

game_parser: ArgumentParser = subcommand(
    "game", new_game, commands, description="Create a blank game to work from."
)

game_parser.add_argument("filename", help="The file to write the new game to")

vault_parser: ArgumentParser = commands.add_parser(
    "vault", description="Create or compile vault files."
)

vault_subcommands: _SubParsersAction = add_subcommands(vault_parser)

new_vault_parser: ArgumentParser = subcommand(
    "new", new_vault, vault_subcommands, description="Create a new vault file."
)

new_vault_parser.add_argument(
    "filename", help="The name for the new vault file"
)

compile_vault_parser: ArgumentParser = subcommand(
    "compile",
    compile_vault,
    vault_subcommands,
    description="Compile an existing vault file.",
)

compile_vault_parser.add_argument(
    "filename",
    metavar="<vault-file>",
    help="The name of the vault file to compile",
)

compile_vault_parser.add_argument(
    "data_file",
    metavar="<data-file>",
    help="The name of the data file to create.",
    nargs="?",
    default=None,
)

map_parser: ArgumentParser = commands.add_parser(
    "map", description="Create or compile maps."
)

map_subcommands: _SubParsersAction = add_subcommands(map_parser)

new_map_parser: ArgumentParser = subcommand(
    "new", new_map, map_subcommands, description="Create a new map."
)

new_map_parser.add_argument(
    "filename", help="The file where the new map will be saved"
)

edit_map_parser: ArgumentParser = subcommand(
    "edit", edit_map, map_subcommands, description="Edit an existing map."
)

edit_map_parser.add_argument(
    "filename", type=Path, help="The map file to edit"
)

crt_parser: ArgumentParser = commands.add_parser(
    "crt", description="Create or edit call response trees."
)

crt_subcommands: _SubParsersAction = add_subcommands(crt_parser)

new_crt_parser: ArgumentParser = subcommand(
    "new",
    new_crt,
    crt_subcommands,
    description="Create a new call response tree.",
)

new_crt_parser.add_argument(
    "filename", help="The file where the new call response tree will be saved"
)

edit_crt_parser: ArgumentParser = subcommand(
    "edit",
    edit_crt,
    crt_subcommands,
    description="Edit an existing call response tree.",
)

edit_crt_parser.add_argument(
    "filename", type=Path, help="The call response tree file to edit"
)


def cmd_main() -> None:
    """Run the earwax client."""
    args = parser.parse_args()
    basicConfig(stream=args.log_file, level=args.log_level)
    return args.func(args)
