"""
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

import pyglet

pyglet.options['shadow_window'] = False

if True:
    from .action import Action
    from .config import Config, ConfigValue
    from .configuration import EarwaxConfig
    from .editor import Editor
    from .event_matcher import EventMatcher
    from .game import Game
    from .level import Level
    from .menu import (ActionMenu, ConfigMenu, FileMenu, Menu, MenuItem,
                       TypeHandler, UnknownTypeError)
    from .sound import (AdvancedInterfaceSoundPlayer,
                        SimpleInterfaceSoundPlayer, get_buffer)
    from .speech import tts
    from .cmd.game_level import GameLevel
    from .cmd.main import cmd_main

__all__ = [
    'Game', 'tts', 'Action', 'Menu', 'MenuItem', 'FileMenu', 'ActionMenu',
    'get_buffer', 'Editor', 'SimpleInterfaceSoundPlayer',
    'AdvancedInterfaceSoundPlayer', 'Level', 'EventMatcher', 'Config',
    'ConfigValue', 'ConfigMenu', 'TypeHandler', 'UnknownTypeError',
    'EarwaxConfig', 'GameLevel', 'cmd_main'
]
