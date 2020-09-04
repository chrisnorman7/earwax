"""Provides the Track class."""

from pathlib import Path
from typing import Optional

from attr import attrs
from synthizer import BufferGenerator, Context, Source

from .sound import play_path


@attrs(auto_attribs=True)
class Track:
    """A track that plays while a :class:`earwax.BoxLevel` object is top of the
    levels stack.

    No panning or fx are applied to ``Track`` instances.

    :ivar ~earwax.Track.sound_path: The track to play.

    :ivar ~earwax.Track.gain: The volume (gain) of the playing sound.

    :ivar ~earwax.Track.generator: The ``synthizer.BufferGenerator`` instance
        to play through.

    :ivar ~earwax.Track.source: The source to route :attr:`self.generator
        <earwax.Track.generator>` through.
    """

    sound_path: Path
    gain: float = 0.25
    generator: Optional[BufferGenerator] = None
    source: Optional[Source] = None

    def load_sound(self, ctx: Context) -> None:
        """Load :attr:`self.sound_path <earwax.Track.sound_path>`."""
        self.generator, self.source = play_path(ctx, self.sound_path)

    def play(self, ctx: Context) -> None:
        """Play this track on a loop.

        To alter how ``sound_path`` is played, override
        :meth:`earwax.Track.load_sound`.

        :param ctx: The ``synthizer.Context`` instance to play through.
        """
        self.load_sound(ctx)
        if self.source is not None:
            self.source.gain = self.gain
        if self.generator is not None:
            self.generator.looping = True

    def stop(self) -> None:
        """Stop this track playing."""
        if self.generator is not None:
            self.generator.destroy()
            self.generator = None
        if self.source is not None:
            self.source.destroy()
            self.source = None
