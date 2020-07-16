"""Provides the sound subsystem."""

import os
import os.path
from random import choice

from attr import Factory, attrib, attrs

from synthizer import Buffer, DirectSource, SynthizerError, BufferGenerator

NoneType = type(None)

buffers = {}


def get_buffer(context, protocol, path):
    """Get a Buffer instance. Buffers are cached in the buffers dictionary, so
    if there is already a buffer with the given protocol and path, it will be
    returned. Otherwise, a new buffer will be created, and added to
    the dictionary."""
    url = f'{protocol}://{path}'
    if url not in buffers:
        buffers[url] = Buffer.from_stream(context, protocol, path)
    return buffers[url]


@attrs
class SimpleInterfaceSoundPlayer:
    """An object which plays a sound whenever its play method is called.

    The same sound will be used, and it will be restarted on each call to play.

    No panning or fx are applied."""

    context = attrib()
    generator = attrib()
    source = attrib(default=Factory(NoneType))

    def play(self):
        """Play the sound."""
        if self.source is None:
            self.source = DirectSource(self.context)
            self.source.add_generator(self.generator)
        self.generator.position = 0

    def __del__(self):
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

    def __init__(self, context, play_files=True, play_directories=True):
        self.play_files = play_files
        self.play_directories = play_directories
        super().__init__(context, None)

    def play(self, path):
        """If self.play_directories evaluates to True, and the given path
        represents a directory, play a random file from the given path.
        Otherwise, if self.play_files evaluates to True, play the given
        path."""
        if self.generator is not None:
            self.generator.destroy()
        if os.path.isdir(path):
            if not self.play_directories:
                return
            path = os.path.join(path, choice(os.listdir(path)))
        elif os.path.isfile(path):
            if not self.play_files:
                return
        else:
            raise NotImplementedError(f'No clue how to play {path}.')
        buffer = get_buffer(self.context, 'file', path)
        self.generator = BufferGenerator(self.context)
        self.generator.buffer = buffer
        if self.source is None:
            self.source = DirectSource(self.context)
        self.source.add_generator(self.generator)
