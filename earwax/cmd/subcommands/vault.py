"""Provides subcommands for working with vault files."""

import os.path
from argparse import Namespace
from glob import glob
from pathlib import Path
from typing import Generator, List, Optional

from cryptography.fernet import Fernet

from ...utils import pluralise
from ...vault_file import VaultFile
from ...yaml import CLoader, load

data: str = """# New vault file
#
# Files can be referenced one of 2 ways:
# Directly, with an absolute path like "sounds", or "music".
# If you provide a path this way, it can either be a file or a directory.
# If you provide a directory, then a list of the files (but not subdirectories)
# will be added.
# The second way is with a glob, like "sounds/*.wav", or "music/*.mp3".
#
#
# You can modify the entries below to add your own files.
files:
#  backstory: backstory.txt
#  maps: maps/*.map
#  sounds: sounds
#
# It is recommended you do not change the key unless you know what you are
# doing.
# This is the key you will need to pass to `VaultFile.from_path` to decrypt
# your data.
#
# Because this file contains your key, it is *highly* recommended that you keep
# it private.
key: {}
"""


def new_vault(args: Namespace) -> None:
    """Create a new vault file."""
    if os.path.isfile(args.filename):
        print('Error:')
        print()
        print(f'File already exists: {args.filename}')
        raise SystemExit
    yaml: str = data.format(Fernet.generate_key().decode())
    with open(args.filename, 'w') as f:
        f.write(yaml)
    print(f'Created a new vault file at {args.filename}.')
    print('You should edit this file, then compile it with')
    filename: str = os.path.splitext(args.filename)[0]
    print(f'`earwax vault compile {filename}.yaml {filename}.data`')


def compile_vault(args: Namespace) -> None:
    """Compile the given vault file."""
    fn: str = args.filename
    if not os.path.isfile(fn):
        print('Error')
        print()
        print(f'File does not exist: {fn}')
        raise SystemExit
    with open(fn, 'r') as f:
        data = load(f, Loader=CLoader)
    if (
        isinstance(data, dict) and
        isinstance(data.get('key', None), str) and
        isinstance(data.get('files', None), dict)
    ):
        files: dict[str, str] = data.get('files', {})
        if not files:
            print('Error:')
            print()
            print(f'The vault file {fn} has an empty files section.')
            raise SystemExit
        vault: VaultFile = VaultFile()
        name: str
        value: str
        for name, value in files.items():
            if not isinstance(name, str):
                print('Error:')
                print()
                print(f'Invalid label: {name}')
                raise SystemExit
            if not isinstance(value, str):
                print('Error:')
                print()
                print(f'Invalid path spec: {value}.')
                raise SystemExit
            print(f'{name}: ', end='')
            g: List[str] = glob(value)
            if len(g) == 1:
                p: Path = Path(g[0])
                vault.add_path(p, label=name)
                print(f'Added 1 {"directory" if p.is_dir() else "file"}.')
            else:
                paths: Generator[Path, None, None] = (Path(x) for x in g)
                num: int = len(g)
                vault.add_path(paths, label=name)
                print(f'Added {num} {pluralise(num, "file")}.')
        data_file: Path
        df: Optional[str] = args.data_file
        if df is None:
            df = os.path.splitext(fn)[0] + '.data'
        data_file = Path(df)
        key_str: str = data['key']
        key: bytes = key_str.encode()
        vault.save(data_file, key)
        print('Data file compiled.')
        print()
        print('To use this file in your code, you can do:')
        print(
            'vault_file: VaultFile = '
            f"VaultFile.from_path(Path('{data_file}'), '{key_str}')"
        )
    else:
        print('Error:')
        print()
        print(f'Does not appear to be a vault file: {fn}')
        if isinstance(data, dict):
            if 'key' not in data:
                print('No encryption key found.')
            elif not isinstance(data.get('files', None), dict):
                print('No files section found.')
            else:
                print('Unknown error.')
