"""Provides the build_surfaces command."""

from argparse import Namespace
from pathlib import Path

from ..constants import surfaces_directory, surfaces_filename

header = '''"""Provides all the surface types."""

from pathlib import Path
'''


def build_surfaces(args: Namespace) -> None:
    s: str = header + '\n'
    surface: Path
    name: str
    for surface in surfaces_directory.iterdir():
        name = surface.name.replace(' ', '_')
        if not name.isidentifier():
            print(f'Error: Invalid surface name {surface.name}.')
            print()
            print('Please consider renaming this directory.')
            raise SystemExit
        path: str = "', '".join(surface.parts)
        s += f"{name}: Path = Path('{path}')\n"
    with surfaces_filename.open('w') as f:
        f.write(s)
    print('Done.')
