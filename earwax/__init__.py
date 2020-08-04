"""Chris's Audio Game Engine

I am writing this so I can use it in my projects. If you find it useful, then
that's great.

You start with the `Game` class."""

from .action import Action
from .editor import Editor
from .game import Game
from .menu import ActionMenu, FileMenu, Menu, MenuItem
from .sound import (AdvancedInterfaceSoundPlayer, SimpleInterfaceSoundPlayer,
                    get_buffer)
from .speech import tts

__all__ = [
    'Game', 'tts', 'Action', 'Menu', 'MenuItem', 'FileMenu', 'ActionMenu',
    'get_buffer', 'Editor', 'SimpleInterfaceSoundPlayer',
    'AdvancedInterfaceSoundPlayer'
]