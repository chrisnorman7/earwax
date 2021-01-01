"""Provides various constants used by the script."""

from pathlib import Path

# Base directory.

cd: Path = Path.cwd()

# Where to store the earwax options.
options_path: Path = cd / 'options.yaml'

# Where to store the main project file.
project_filename: Path = cd / 'project.yaml'

# Directory where maps are stored.
maps_directory: Path = cd / 'maps'

# The main sounds directory.
sounds_directory: Path = cd / 'sounds'

# The directory where surface directories are stored.
surfaces_directory: Path = sounds_directory / 'surfaces'

# The directory where ambiances are stored.
ambiances_directory: Path = sounds_directory / 'ambiances'

# The directory where music files are store.
music_directory: Path = sounds_directory / 'music'

# Where to store the surfaces.py file.
surfaces_filename: Path = cd / 'surfaces.py'
