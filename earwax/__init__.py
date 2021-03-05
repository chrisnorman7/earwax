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

    pyglet.options["shadow_window"] = False
except (ImportError, TypeError):
    pyglet = None  # Docs are building.

from . import conversation_level, hat_directions, story, types, utils
from .action import Action
from .action_map import ActionMap
from .ambiance import Ambiance
from .config import Config, ConfigValue
from .configuration import EarwaxConfig
from .credit import Credit
from .dialogue_tree import DialogueLine, DialogueTree
from .die import Die
from .editor import Editor, TextValidator
from .event_matcher import EventMatcher
from .game import Game, GameNotRunning
from .game_board import GameBoard, NoSuchTile
from .input_modes import InputModes
from .level import IntroLevel, Level
from .mapping import (Box, BoxBounds, BoxLevel, BoxTypes, CurrentBox, Door,
                      MapEditor, MapEditorContext, NearestBox, NotADoor,
                      Portal)
from .menus import (ActionMenu, ConfigMenu, FileMenu, Menu, MenuItem,
                    ReverbEditor, TypeHandler, UnknownTypeError)
from .mixins import DismissibleMixin, DumpLoadMixin, TitleMixin
from .networking import (
    AlreadyConnected, AlreadyConnecting, ConnectionStates, NetworkConnection,
    NetworkingConnectionError, NotConnectedYet)
from .point import Point, PointDirections
from .promises import (Promise, PromiseStates, StaggeredPromise,
                       ThreadedPromise, staggered_promise)
from .reverb import Reverb
from .rumble_effects import RumbleEffect, RumbleSequence, RumbleSequenceLine
from .sound import (AlreadyDestroyed, BufferCache, BufferDirectory, NoCache,
                    Sound, SoundError, SoundManager)
from .speech import tts
from .task import IntervalFunction, Task, TaskFunction
from .track import Track, TrackTypes
from .vault_file import IncorrectVaultKey, VaultFile
from .walking_directions import walking_directions

# This next import is intentionally separated from the rest, to prevent
# circular imports.
if True:
    from . import cmd
