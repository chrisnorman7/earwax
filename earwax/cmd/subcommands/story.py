"""Provides the story subcommand."""

import os
from argparse import Namespace
from xml.etree.ElementTree import Element

try:
    from pyglet.window import Window
except ModuleNotFoundError:
    Window = object
from xml_python import Builder, UnhandledElement

from earwax import Game
from earwax.story import (EditLevel, StoryContext, StoryWorld, WorldRoom,
                          world_builder)


def play_story(args: Namespace, edit: bool = False) -> None:
    """Load and play a story."""
    filename: str = args.filename
    if not os.path.isfile(filename):
        print('File not found.')
        print()
        print(f'There is no file named {filename}.')
        raise SystemExit
    try:
        world: StoryWorld = world_builder.handle_filename(filename)
    except (RuntimeError, UnhandledElement) as e:
        print('Error loading story:')
        print()
        if isinstance(e, RuntimeError):
            print(e)
        else:
            assert isinstance(e, UnhandledElement)
            builder: Builder
            element: Element
            builder, element = e.args
            print(
                'You cannot use a <%s> tag inside of a <%s> tag.' % (
                    element.tag, builder.name
                )
            )
        raise SystemExit
    game: Game = Game(name=world.name)
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
        w: StoryWorld = StoryWorld(name='Untitled World')
        r: WorldRoom = WorldRoom(w, 'first_room')
        w.rooms[r.id] = r
        w.initial_room_id = r.id
        with open(filename, 'w') as f:
            f.write(w.to_string())
        print('Created %s.' % w.name)


def edit_story(args: Namespace) -> None:
    """Edit the given story."""
    return play_story(args, edit=True)
