"""Provides various constants used by the script."""

from pathlib import Path

# Base directory.

cd: Path = Path.cwd()

# Where to store the earwax options.
options_path: Path = cd / "options.yaml"

# Where to store the main project file.
project_filename: Path = cd / "project.yaml"

# Directory where maps are stored.
maps_directory: Path = cd / "maps"

# Directory where scripts are stored.
scripts_directory: Path = cd / "scripts"
