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

from typing import List

try:
    import pyglet
    pyglet.options['shadow_window'] = False
except (ImportError, TypeError):
    pyglet = None  # Docs are building.

from . import hat_directions, types, utils
from .action import Action
from .action_map import ActionMap
from .ambiance import Ambiance
from .config import Config, ConfigValue
from .configuration import EarwaxConfig
from .credit import Credit
from .dialogue_tree import DialogueLine, DialogueTree
from .die import Die
from .editor import Editor
from .event_matcher import EventMatcher
from .game import Game, GameNotRunning
from .game_board import GameBoard, NoSuchTile
from .level import IntroLevel, Level
from .mapping import (Box, BoxBounds, BoxLevel, BoxTypes, CurrentBox, Door,
                      NearestBox, NotADoor, Portal, ReverbSettingsDict)
from .menu import (ActionMenu, ConfigMenu, FileMenu, Menu, MenuItem,
                   TypeHandler, UnknownTypeError)
from .mixins import CoordinatesMixin, DismissibleMixin, TitleMixin
from .networking import (AlreadyConnected, AlreadyConnecting, ConnectionError,
                         ConnectionStates, NetworkConnection, NotConnectedYet)
from .point import Point, PointDirections
from .promises import (Promise, PromiseStates, StaggeredPromise,
                       ThreadedPromise, staggered_promise)
from .rumble_effects import RumbleEffect, RumbleSequence, RumbleSequenceLine
from .sound import (AlreadyDestroyed, BufferCache, BufferDirectory, NoCache,
                    Sound, SoundError, SoundManager)
from .speech import tts
from .task import IntervalFunction, Task, TaskFunction
from .track import Track, TrackTypes
from .walking_directions import walking_directions

__all__: List[str] = [
    # General modules:
    'hat_directions', 'types', 'utils',
    # action.py:
    'Action',
    # action_map.py:
    'ActionMap',
    # ambiance.py:
    'Ambiance',
    # config.py:
    'Config', 'ConfigValue',
    # configuration.py:
    'EarwaxConfig',
    # credit.py:
    'Credit',
    # dialogue_tree.py:
    'DialogueLine', 'DialogueTree',
    # die.py:
    'Die',
    # editor.py:
    'Editor',
    # event_matcher.py:
    'EventMatcher',
    # game.py:
    'Game', 'GameNotRunning',
    # game_board.py:
    'GameBoard', 'NoSuchTile',
    # level.py:
    'IntroLevel', 'Level',
    # mapping/__init__.py:
    'Box', 'BoxBounds', 'BoxLevel', 'BoxTypes', 'CurrentBox', 'Door',
    'NearestBox', 'NotADoor', 'Portal', 'ReverbSettingsDict',
    # menu/__init__.py:
    'ActionMenu', 'ConfigMenu', 'FileMenu', 'Menu', 'MenuItem', 'TypeHandler',
    'UnknownTypeError',
    # mixins.py:
    'CoordinatesMixin', 'DismissibleMixin', 'TitleMixin',
    # networking.py:
    'AlreadyConnected', 'AlreadyConnecting', 'ConnectionError',
    'ConnectionStates', 'NetworkConnection', 'NotConnectedYet',
    # point.py:
    'Point', 'PointDirections',
    # promises/__init__.py:
    'Promise', 'PromiseStates', 'StaggeredPromise', 'ThreadedPromise',
    'staggered_promise',
    # rumble_effects.py:
    'RumbleEffect', 'RumbleSequence', 'RumbleSequenceLine',
    # sound.py:
    'AlreadyDestroyed', 'BufferCache', 'BufferDirectory', 'NoCache', 'Sound',
    'SoundError', 'SoundManager',
    # speech.py:
    'tts',
    # task.py:
    'IntervalFunction', 'Task', 'TaskFunction',
    # track.py:
    'Track', 'TrackTypes',
    # walking_directions.py:
    'walking_directions',
]
