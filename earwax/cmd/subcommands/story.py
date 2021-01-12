"""Provides the story subcommand."""

import os
from argparse import Namespace
from logging import Logger, getLogger

try:
    from pyglet.window import Window
except ModuleNotFoundError:
    Window = object

from ...game import Game
from ...story import EditLevel, StoryContext, StoryWorld, WorldRoom

logger: Logger = getLogger(__name__)


def play_story(args: Namespace, edit: bool = False) -> None:
    """Load and play a story."""
    filename: str = args.filename
    logger.info('Attempting to load worl file %s.', filename)
    if not os.path.isfile(filename):
        print('File not found.')
        print()
        print(f'There is no file named {filename}.')
        raise SystemExit
    game: Game = Game()
    world: StoryWorld = StoryWorld.from_filename(filename, game)
    game.name = world.name
    ctx: StoryContext
    try:
        ctx = StoryContext(game, world, edit=edit)
    except RuntimeError as e:
        print('Error creating story level:')
        print()
        print(e)
        raise SystemExit
    caption: str = world.name
    if edit:
        caption += f' ({filename})'
        assert isinstance(ctx.main_level, EditLevel), (
            'Invalid level %r' % ctx.main_level
        )
        ctx.main_level.filename = filename
    window: Window = Window(caption=caption)
    game.run(window, initial_level=ctx.get_main_menu())


def create_story(args: Namespace) -> None:
    """Create a new story."""
    filename: str = args.filename
    if os.path.exists(filename):
        print('Error: Path already exists: %s.' % filename)
        print()
        print('Perhaps you meant the `story play` subcommand?')
    else:
        game: Game = Game()
        w: StoryWorld = StoryWorld(game, name='Untitled World')
        r: WorldRoom = WorldRoom(id='first_room', name='first_room')
        w.add_room(r)
        w.initial_room_id = r.id
        w.save(filename)
        print('Created %s.' % w.name)


def edit_story(args: Namespace) -> None:
    """Edit the given story."""
    return play_story(args, edit=True)
