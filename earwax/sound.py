"""Provides the sound subsystem."""

from pathlib import Path
from random import choice
from typing import Dict

from attr import attrs

from synthizer import (Buffer, BufferGenerator, Context, DirectSource,
                       Generator, Source, SynthizerError)

buffers: Dict[str, Buffer] = {}


def get_buffer(protocol: str, path: str) -> Buffer:
    """Get a Buffer instance. Buffers are cached in the buffers dictionary, so
    if there is already a buffer with the given protocol and path, it will be
    returned. Otherwise, a new buffer will be created, and added to
    the dictionary."""
    url: str = f'{protocol}://{path}'
    if url not in buffers:
        buffers[url] = Buffer.from_stream(protocol, path)
    return buffers[url]


@attrs(auto_attribs=True)
class SimpleInterfaceSoundPlayer:
    """An object which plays a sound whenever its play method is called.

    The same sound will be used, and it will be restarted on each call to play.

    No panning or fx are applied."""

    # The audio context to use.
    context: Context

    # The generator to use.
    generator: Generator

    # The source to play through.
    source: Source = None

    def play(self) -> None:
        """Play the sound."""
        if self.source is None:
            self.source = DirectSource(self.context)
            self.source.add_generator(self.generator)
        self.generator.position = 0

    def __del__(self) -> None:
        """Destroy the source and the generator."""
        try:
            if self.generator is not None:
                self.generator.destroy()
            if self.source is not None:
                self.source.destroy()
        except SynthizerError:
            pass  # They're already gone.


class AdvancedInterfaceSoundPlayer(SimpleInterfaceSoundPlayer):
    """An interface player whose play method takes extra arguments."""

    def __init__(
        self, context: Context, play_files: bool = True,
        play_directories: bool = True
    ) -> None:
        self.play_files = play_files
        self.play_directories = play_directories
        super().__init__(context, None)

    def play_path(self, path: Path) -> None:
        """If self.play_directories evaluates to True, and the given path
        represents a directory, play a random file from the given path.
        Otherwise, if self.play_files evaluates to True, play the given
        path."""
        if self.generator is not None:
            self.generator.destroy()
            self.generator = None
        if path.is_dir():
            if not self.play_directories:
                return
            path = path / choice(list(path.iterdir()))
            if not path.is_file():
                return  # Don't go through more directories.
        elif path.is_file():
            if not self.play_files:
                return
        else:
            raise NotImplementedError(f'No clue how to play {path}.')
        buffer = get_buffer('file', str(path))
        self.generator = BufferGenerator(self.context)
        self.generator.buffer = buffer
        if self.source is None:
            self.source = DirectSource(self.context)
        self.source.add_generator(self.generator)
