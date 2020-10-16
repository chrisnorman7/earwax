"""Provides the Ambiance class."""

from typing import TYPE_CHECKING

from attr import attrs

if TYPE_CHECKING:
    from synthizer import Context

from .point import Point
from .sound import play_path
from .track import Track


@attrs(auto_attribs=True)
class Ambiance(Track):
    """A class that represents a stationary sound on a map.

    :ivar ~earwax.Ambiance.coordinates: The coordinates of this ambiance.
    """

    coordinates: Point = Point(0, 0, 0)

    def load_sound(self, ctx: 'Context') -> None:
        """Load the sound, passing a position argument."""
        self.generator, self.source = play_path(
            ctx, self.sound_path, position=self.coordinates.coordinates
        )
