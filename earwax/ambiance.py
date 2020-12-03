"""Provides the Ambiance class."""

from typing import Optional

from attr import Factory, attrib, attrs
from synthizer import Context, Source3D, StreamingGenerator

from .point import Point


@attrs(auto_attribs=True)
class Ambiance:
    """A class that represents a positioned sound on a map.

    The sound can be moved by way of the :meth:`~earwax.Ambiance.set_position`
    method.

    :ivar ~earwax.Ambiance.protocol: The ``protocol`` argument to pass to
        ``synthizer.StreamingGenerator````.

    :ivar ~earwax.Ambiance.path: The ``path`` argument to pass to
        ``synthizer.StreamingGenerator``.

    :ivar ~earwax.Ambiance.coordinates: The coordinates of this ambiance.

    :ivar ~earwax.Ambiance.generator: The ``synthizer.BufferGenerator``
        instance to play through.

        This value is initialised as part of the :meth:`~earwax.Ambiance.play`
        method.

    :ivar ~earwax.Ambiance.source: The source to play through.

        This value is initialised as part of the :meth:`~earwax.Ambiance.play`
        method, and is used by the :meth:`~earwax.Ambiance.set_position` method
        to update the position of the sound being played.
    """

    protocol: str
    path: str
    coordinates: Point = Point(0, 0, 0)
    generator: Optional[StreamingGenerator] = attrib(
        default=Factory(type(None)), init=False
    )
    source: Optional[Source3D] = attrib(
        default=Factory(type(None)), init=False
    )

    def play(self, ctx: Context, gain: float) -> None:
        """Load and position the sound."""
        self.source = Source3D(ctx)
        self.source.gain = gain
        self.set_position(self.coordinates)
        self.generator = StreamingGenerator(ctx, self.protocol, self.path)
        self.generator.looping = True
        self.source.add_generator(self.generator)

    def stop(self) -> None:
        """Stop this ambiance playing."""
        if self.generator is not None:
            self.generator.destroy()
            self.generator = None
        if self.source is not None:
            self.source.destroy()
            self.source = None

    def set_position(self, pos: Point) -> None:
        """Move this ambiance.

        This method should be used instead of setting :attr:`self.coordinates
        <earwax.Ambiance.coordinates>` directly, as this method will also
        update the position of :attr:`self.source <earwax.Ambiance.source>`.

        :param pos: The new position.
        """
        self.coordinates = pos
        if self.source is not None:
            self.source.position = pos.coordinates
