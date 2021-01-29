"""Test the VaultFile class."""

from pathlib import Path
from typing import List

from pytest import raises

from earwax import IncorrectVaultKey, VaultFile


def test_init() -> None:
    """Test initialisation."""
    v: VaultFile = VaultFile()
    assert v.entries == {}


def test_add_path() -> None:
    """Test adding paths."""
    v: VaultFile = VaultFile()
    assert v.add_path(Path('sound.wav')) == 'sound.wav'
    assert isinstance(v.entries['sound.wav'], bytes)
    with open('sound.wav', 'rb') as f:
        assert v.entries['sound.wav'] == f.read()
    label: str = 'test label'
    assert v.add_path(Path('sound.wav'), label=label) == label
    assert isinstance(v.entries[label], bytes)
    assert v.entries[label] == v.entries['sound.wav']
    p: Path = Path('earwax')
    files: List[Path] = [x for x in p.iterdir() if x.is_file()]
    label = v.add_path(p.iterdir(), label='earwax')
    assert label == 'earwax'
    assert isinstance(v.entries[label], list)
    assert len(files) > 1
    assert len(v.entries[label]) == len(files)
    assert isinstance(v.entries[label][0], bytes)
    i: int
    expected: object
    for i, expected in enumerate(v.entries[label]):
        child: Path = files[i]
        assert isinstance(expected, bytes)
        with child.open('rb') as f:
            data: bytes = f.read()
            assert expected == data, f'File #{i} ({child}) does not match.'
    label = 'test directory'
    assert v.add_path(Path('earwax'), label=label) == label
    assert v.entries[label] == v.entries['earwax']
    assert v.add_path(Path('tests')) == 'tests'


def test_save(valid_key: bytes) -> None:
    """Test the save method."""
    v: VaultFile = VaultFile()
    v.add_path(Path('earwax'))
    filename: Path = Path('earwax.data')
    v.save(filename, valid_key)
    assert filename.is_file()
    with filename.open('rb') as f:
        data: bytes = f.read()
    assert isinstance(data, bytes)
    assert len(data) > 100
    filename.unlink()


def test_load(valid_key: bytes, invalid_key: bytes) -> None:
    """Test loading a vault."""
    v1: VaultFile = VaultFile()
    v1.add_path(Path('earwax'))
    v1.add_path(Path('tests'))
    filename: Path = Path('test.data')
    v1.save(filename, valid_key)
    with raises(IncorrectVaultKey) as exc:
        VaultFile.from_path(filename, invalid_key)
    assert exc.value.args == (filename,)
    v2: VaultFile = VaultFile.from_path(filename, valid_key)
    assert v1 == v2
    filename.unlink()
