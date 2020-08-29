"""Provides various constants used by the script."""

from pathlib import Path

# Where to store the earwax options.
options_file: Path = Path('options.yaml')

# Where to store the main workspace file.
workspace_file: Path = Path('workspace.yaml')

# The main sounds directory.
sounds_directory: Path = Path('sounds')

# The directory where surface directories are stored.
surfaces_directory: Path = sounds_directory / 'surfaces'

# The directory where ambiances are stored.
ambiances_directory: Path = sounds_directory / 'ambiances'

# The directory where music files are store.
music_directory: Path = sounds_directory / 'music'

# The directory where level files are stored.
levels_directory: Path = Path('levels')
