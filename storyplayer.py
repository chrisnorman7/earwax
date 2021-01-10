"""A script for interracting with story files."""

from argparse import ArgumentParser, Namespace, _MutuallyExclusiveGroup

from earwax.cmd.subcommands.story import create_story, play_story

parser: ArgumentParser = ArgumentParser(description=__doc__)

group: _MutuallyExclusiveGroup = parser.add_mutually_exclusive_group()

group.add_argument(
    '-p', '--play', action='store_true',
    help='Play a world'
)
group.add_argument(
    '-c', '--create', action='store_true',
    help='Create a new world'
)
group.add_argument(
    '-e', '--edit', action='store_true',
    help='Edit a world'
)

parser.add_argument(
    'filename', metavar='<filename>',
    help='The file to open'
)


if __name__ == '__main__':
    args: Namespace = parser.parse_args()
    if args.create:
        create_story(args)
    else:
        play_story(args, edit=args.edit)
