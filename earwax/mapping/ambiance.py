"""Provides the Ambiance class."""

from pathlib import Path
from typing import Optional, Tuple

from attr import attrs
from synthizer import BufferGenerator, Context, Source3D

from ..sound import get_buffer
from .box_level import BoxLevel


@attrs(auto_attribs=True)
class Ambiance:
    """A class that represents a stationary sound on a map.

    :ivar ~earwax.Ambiance.level: The box level to attach the ambiance to.

    :ivar ~earwax.Ambiance.x: The x coordinate.

    :ivar ~earwax.Ambiance.y: The y coordinate.

    :ivar ~earwax.Ambiance.sound_path: The path to the sound that shouldplay.

    :ivar ~earwax.Ambiance.gain: The volume (gain) of the playing sound.

    :ivar ~earwax.Ambiance.generator: The generator that the sound will play
        through.

    :ivar ~earwax.Ambiance.source: The source that
        :attr:`~earwax.Ambiance.generator` will be connected to.
    """

    level: BoxLevel
    x: float
    y: float
    SOUND_path: Path
    gain: float = 0.25

    generator: Optional[BufferGenerator] = None
    source: Optional[Source3D] = None

    @property
    def coordinates(self) -> Tuple[float, float]:
        """Returns the coordinates of this ambiance as a tuple."""
        return self.x, self.y

    def start(self) -> None:
        """Start the sound playing."""
        ctx: Context = self.level.game.audio_context  # Reduce typing.
        if ctx is not None:
            self.source = Source3D(ctx)
            self.source.gain = self.gain
            self.source.position = self.x, self.y, 0.0
            self.generator = BufferGenerator(ctx)
            self.generator.buffer = get_buffer('file', str(self.SOUND_path))
            self.generator.looping = True
            self.source.add_generator(self.generator)

    def stop(self) -> None:
        """Stop the sound."""
        if self.generator is not None:
            self.generator.destroy()
            self.generator = None
        if self.source is not None:
            self.source.destroy()
            self.source = None
