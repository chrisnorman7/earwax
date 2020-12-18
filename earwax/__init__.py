"""The Earwax game engine.

Earwax
------

    This package is heavily inspired by `Flutter <https://flutter.dev/>`_.

Usage
=====

* Begin with a :class:`~earwax.Game` object::

    from earwax import Game, Level
    g = Game()

* Create a level::

    l = Level()

* Add actions to allow the player to do things::

    @l.action(...)
    def action():
        pass

* Create a Pyglet window::

    from pyglet.window import Window
    w = Window(caption='Earwax Game')

* Run the game you have created::

    g.run(w)

There are ready made :class:`~earwax.Level` classes for creating :class:`menus
<earwax.Menu>`, and :class:`editors <earwax.Editor>`.
"""

try:
    import pyglet
    pyglet.options['shadow_window'] = False
except (ImportError, TypeError):
    pass  # Docs are building.

if True:
    from . import types, utils
    from .action import Action
    from .ambiance import Ambiance
    from .config import Config, ConfigValue
    from .configuration import EarwaxConfig
    from .die import Die
    from .editor import Editor
    from .event_matcher import EventMatcher
    from .game import Game, GameNotRunning
    from .game_board import GameBoard, NoSuchTile
    from .level import IntroLevel, Level
    from .mapping import (Box, BoxBounds, BoxLevel, BoxSound, BoxTypes, Door,
                          NotADoor, OutOfBounds, Portal)
    from .menu import (ActionMenu, ConfigMenu, FileMenu, Menu, MenuItem,
                       TypeHandler, UnknownTypeError)
    from .mixins import CoordinatesMixin, DismissibleMixin, TitleMixin
    from .networking import (AlreadyConnected, AlreadyConnecting,
                             ConnectionError, ConnectionStates,
                             NetworkConnection, NotConnectedYet)
    from .point import Point, PointDirections
    from .promises import (Promise, PromiseStates, StaggeredPromise,
                           ThreadedPromise, staggered_promise)
    from .sound import (AdvancedInterfaceSoundPlayer, BufferDirectory,
                        SimpleInterfaceSoundPlayer, get_buffer,
                        play_and_destroy, play_path, play_paths,
                        schedule_generator_destruction)
    from .speech import tts
    from .task import IntervalFunction, Task, TaskFunction
    from .track import Track, TrackTypes
    from .walking_directions import walking_directions

# The below imports are intentionally separated from those above, to avoid
# errors when trying to import half-initialised modules.
if True:
    from .cmd.main import cmd_main
    from .cmd.project import Project
    from .cmd.project_level import ProjectLevel

__all__ = [
    'Game', 'tts', 'Action', 'Menu', 'MenuItem', 'FileMenu', 'ActionMenu',
    'get_buffer', 'Editor', 'SimpleInterfaceSoundPlayer',
    'AdvancedInterfaceSoundPlayer', 'Level', 'EventMatcher', 'Config',
    'ConfigValue', 'ConfigMenu', 'TypeHandler', 'UnknownTypeError',
    'EarwaxConfig', 'ProjectLevel', 'cmd_main', 'Project', 'Box', 'Point',
    'OutOfBounds', 'PointDirections', 'walking_directions', 'BoxTypes',
    'play_path', 'schedule_generator_destruction', 'BoxLevel', 'Ambiance',
    'Door', 'NotADoor', 'play_and_destroy', 'Portal', 'Track', 'play_paths',
    'DismissibleMixin', 'TitleMixin', 'IntroLevel', 'CoordinatesMixin',
    'GameBoard', 'NoSuchTile', 'Die', 'BufferDirectory', 'PromiseStates',
    'ThreadedPromise', 'StaggeredPromise', 'staggered_promise', 'Promise',
    'types', 'utils', 'GameNotRunning', 'NetworkConnection',
    'ConnectionStates', 'ConnectionError', 'AlreadyConnected',
    'AlreadyConnecting', 'NotConnectedYet', 'TrackTypes', 'Task',
    'TaskFunction', 'IntervalFunction', 'BoxBounds', 'BoxSound'
]
