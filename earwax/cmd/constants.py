"""Provides various constants for the earwax script."""

from pathlib import Path

from pyglet.resource import get_settings_path

from earwax import Game

game: Game = Game()

settings_path: Path = Path(get_settings_path('earwax'))
