"""Provides the story subcommand."""

import os
from argparse import Namespace
from xml.etree.ElementTree import Element

try:
    from pyglet.window import Window
except ModuleNotFoundError:
    Window = object
from xml_python import Builder, UnhandledElement

from earwax import Game, StoryContext
from earwax.story import StoryWorld, world_builder


def play_story(args: Namespace) -> None:
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
        ctx = StoryContext(game, world)
    except RuntimeError as e:
        print('Error creating story level:')
        print()
        print(e)
        raise SystemExit
    window: Window = Window(caption=world.name)
    game.run(window, initial_level=ctx.get_main_menu())