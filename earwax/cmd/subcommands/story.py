"""Provides the story subcommand."""

import os.path
from argparse import Namespace
from logging import Logger, getLogger
from pathlib import Path
from shutil import copy
from typing import List, Union

from jinja2 import Environment, Template

from ...game import Game
from ...pyglet import Window
from ...story import (EditLevel, RoomExit, RoomObject, StoryContext,
                      StoryWorld, WorldAction, WorldAmbiance, WorldRoom)

code: str = '''"""{{ world.name }}.

Author: {{ world.author }}
Filename: {{ filename }}
"""

from io import StringIO

from earwax import Game
from earwax.story import StoryContext, StoryWorld
from pyglet.window import Window

if __name__ == '__main__':
    f: StringIO = StringIO({{ data }})
    game: Game = Game()
    world: StoryWorld = StoryWorld.from_file(f, game)
    ctx: StoryContext = StoryContext(game, world, edit=False)
    window: Window = Window(caption=ctx.get_window_caption())
    game.run(window, initial_level=ctx.get_main_menu())

'''


def make_directory(directory: Path) -> None:
    """Make the given directory, if necessary.

    if the given directory already exists, print a message to that effect.

    Otherwise, create the directory, and print a message about it.

    :param directory: The directory to create.
    """
    if directory.is_dir():
        print(f'The directory {directory} already exists.')
    else:
        print(f'Creating directory {directory}.')
        directory.mkdir()


def copy_path(source: Union[str, Path], destination: Path) -> str:
    """Copy the given file or folder to the given destination.

    :param source: Where to copy from.

    :param destination: The destination for the new file.
    """
    if destination.is_file():
        print(f'Not copying {source}: Destination already exists.')
        return str(destination)
    else:
        print(f'{source} -> {destination}')
        return str(copy(source, destination))


def get_filename(filename: str, index: int) -> str:
    """Return a unique filename.

    Given a filename of ``'music/track.wav'``, and an index of ``5``,
    ``'5.wav'`` would be returned.

    :param filename: The original filename (can include path).

    :param index: The index of this filename in whatever list is being iterated
        over.
    """
    return f'{index}{os.path.splitext(filename)[1]}'


def copy_ambiances(ambiances: List[WorldAmbiance], destination: Path) -> None:
    """Copy all ambiance files.

    :param ambiances: The ambiances whose sounds will be copied.

    :param destination: The ambiances directory to copy into.

        If this directory does not exist, it will be created before copying
        begins.
    """
    make_directory(destination)
    for index, ambiance in enumerate(ambiances):
        filename = get_filename(ambiance.path, index)
        filename = copy_path(ambiance.path, destination / filename)
        ambiance.path = filename


def copy_actions(actions: List[WorldAction], destination: Path) -> None:
    """Copy the sounds from a list of action objects.

    :param actions: The list of actions whose sounds will be copied.

    :param destination: The destination for the copied sounds.

        If this directory does not exist, it will be created before the copy.
    """
    action: WorldAction
    for index, action in enumerate(actions):
        copy_action(action, destination, index)


def copy_action(action: WorldAction, destination: Path, index: int) -> None:
    """Copy the sound for the given action.

    :param action: The action whose sound will be copied.

    :param destination: The destination the sound will be copied to.

        If this directory does not exist, it will be created before the copy.

    :param index: The number to base the resulting file name on.
    """
    make_directory(destination)
    if action.sound is not None:
        filename = get_filename(action.sound, index)
        action.sound = copy_path(
            action.sound, destination / filename
        )


def build_story(args: Namespace) -> None:
    """Build the world."""
    world_filename: str = args.world_filename
    python_filename: str = args.python_filename
    if not os.path.isfile(world_filename):
        print('Invalid world file %s: File does not exist.' % world_filename)
        raise SystemExit
    game: Game = Game()
    print(f'Loading game from {world_filename}.')
    with open(world_filename, 'r') as in_file:
        world: StoryWorld = StoryWorld.from_file(in_file, game)
    sounds_directory: Path = Path('story_sounds')
    make_directory(sounds_directory)
    print('Gathering assets:')
    music_directory = sounds_directory / 'music'
    make_directory(music_directory)
    musics: List[str] = world.main_menu_musics
    world.main_menu_musics = []
    index: int
    music: str
    for index, music in enumerate(musics):
        filename: str = get_filename(music, index)
        filename = copy_path(music, music_directory / filename)
        world.main_menu_musics.append(filename)
    if world.cursor_sound is None:
        print('Skipping empty cursor sound.')
    else:
        world.cursor_sound = copy_path(world.cursor_sound, sounds_directory)
    if world.empty_category_sound is None:
        print('Skipping empty category sound.')
    else:
        world.empty_category_sound = copy_path(
            world.empty_category_sound, sounds_directory
        )
    actions_directory: Path = sounds_directory / 'actions'
    if world.take_action is not None:
        copy_action(world.take_action, actions_directory, 0)
    if world.drop_action is not None:
        copy_action(world.drop_action, actions_directory, 1)
    rooms_directory: Path = sounds_directory / 'rooms'
    make_directory(rooms_directory)
    room: WorldRoom
    action: WorldAction
    for room in world.rooms.values():
        room_directory: Path = rooms_directory / room.id
        make_directory(room_directory)
        ambiances_directory: Path = room_directory / 'ambiances'
        copy_ambiances(room.ambiances, ambiances_directory)
        exits_directory: Path = room_directory / 'exits'
        x: RoomExit
        actions: List[WorldAction] = [x.action for x in room.exits]
        copy_actions(actions, exits_directory)
        obj: RoomObject
        objects_directory: Path = room_directory / 'objects'
        make_directory(objects_directory)
        for obj in room.objects.values():
            object_directory: Path = objects_directory / obj.id
            make_directory(object_directory)
            ambiances_directory = object_directory / 'ambiances'
            copy_ambiances(obj.ambiances, ambiances_directory)
            actions_directory = object_directory / 'actions'
            copy_actions(obj.actions, actions_directory)
            system_actions_directory: Path = actions_directory / 'system'
            if obj.take_action is not None:
                copy_action(obj.take_action, system_actions_directory, 0)
            if obj.drop_action is not None:
                copy_action(obj.drop_action, system_actions_directory, 1)
            if obj.use_action is not None:
                copy_action(obj.use_action, system_actions_directory, 2)
            if obj.actions_action is not None:
                copy_action(obj.actions_action, system_actions_directory, 3)
    yaml_file: Path = Path(python_filename + '.yaml')
    print(f'Dumping temporary world to {yaml_file}.')
    world.save(yaml_file)
    print('Loading YAML.')
    with yaml_file.open('r') as f:
        yaml: str = f.read()
    data: str = repr(yaml)
    e: Environment = Environment()
    t: Template = e.from_string(code)
    source: str = t.render(filename=world_filename, world=world, data=data)
    with open(python_filename, 'w') as out_file:
        out_file.write(source)
        print('Done.')


def play_story(args: Namespace, edit: bool = False) -> None:
    """Load and play a story."""
    suffix: str
    if edit:
        suffix = 'edit_story'
    else:
        suffix = 'play_story'
    logger: Logger = getLogger(f'{__name__}.{suffix}')
    filename: Path = Path(args.filename)
    logger.info('Attempting to load worl file %s.', filename)
    if not filename.is_file():
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
        assert isinstance(ctx.main_level, EditLevel), (
            'Invalid level %r' % ctx.main_level
        )
    ctx.main_level.filename = filename
    window: Window = Window(caption=ctx.get_window_caption())
    game.run(window, initial_level=ctx.get_main_menu())


def create_story(args: Namespace) -> None:
    """Create a new story."""
    filename: Path = Path(args.filename)
    if filename.exists():
        print('Error: Path already exists: %s.' % filename)
        print()
        print('Perhaps you meant the `story play` subcommand?')
    else:
        game: Game = Game()
        w: StoryWorld = StoryWorld(game, name='Untitled World')
        r: WorldRoom = WorldRoom(id='first_room', name='first_room')
        w.add_room(r)
        w.save(filename)
        print('Created %s.' % w.name)


def edit_story(args: Namespace) -> None:
    """Edit the given story."""
    return play_story(args, edit=True)
