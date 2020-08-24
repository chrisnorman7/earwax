"""Provides various constants for the earwax script."""

from pathlib import Path

from pyglet.resource import get_settings_path

from earwax import Game

game: Game = Game()

settings_path_str: str = get_settings_path('earwax')
settings_path: Path

if isinstance(settings_path_str, str):
    settings_path = Path()
else:
    settings_path = Path.cwd()
