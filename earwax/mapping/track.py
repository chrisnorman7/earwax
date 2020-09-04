"""Provides the Track class."""

from pathlib import Path
from typing import Optional

from attr import attrs
from synthizer import BufferGenerator, Context, DirectSource

from ..sound import play_path


@attrs(auto_attribs=True)
class Track:
    """A track that plays while a :class:`earwax.BoxLevel` object is top of the
    levels stack.

    No panning or fx are applied to ``Track`` instances.
    """

    sound_path: Path
    generator: Optional[BufferGenerator] = None
    source: Optional[DirectSource] = None

    def play(self, ctx: Context) -> None:
        """Play this track on a loop.

        :param ctx: The ``synthizer.Context`` instance to play through.
        """
        self.buffer, self.source = play_path(ctx, self.sound_path)
        self.buffer.looping = True

    def stop(self) -> None:
        """Stop this track playing."""
        if self.generator is not None:
            self.generator.destroy()
            self.generator = None
        if self.source is not None:
            self.source.destroy()
            self.source = None
