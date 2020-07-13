"""Chris's Audio Game Engine

I am writing this so I can use it in my projects. If you find it useful, then
that's great.

You start with the `Game` class."""

from .game import Game
from .speech import tts
from .action import Action

__all__ = ['Game', 'tts', 'Action']
