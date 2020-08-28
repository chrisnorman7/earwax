"""Provides various constants used by the script."""

from pathlib import Path

# Where to store the earwax options.
options_file: Path = Path('options.yaml')

# Where to store the main game file.
game_file: Path = Path('game.yaml')

# The directory to store sounds in.
sounds_directory: Path = Path('sounds')

# The directory where surface directory are found.
surfaces_directory: Path = sounds_directory / 'surfaces'
