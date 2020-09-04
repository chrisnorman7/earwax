"""Provides the Ambiance class."""

from typing import Tuple

from attr import attrs
from synthizer import Context

from .sound import play_path
from .track import Track


@attrs(auto_attribs=True)
class AmbianceBase:
    """Add coordinates."""
    x: float
    y: float
    z: float

    @property
    def coordinates(self) -> Tuple[float, float, float]:
        """Returns the coordinates of this ambiance as a tuple."""
        return self.x, self.y, self.z


@attrs(auto_attribs=True)
class Ambiance(AmbianceBase, Track):
    """A class that represents a stationary sound on a map.

    :ivar ~earwax.Ambiance.point: The coordinates of this ambiance.
    """

    def load_sound(self, ctx: Context) -> None:
        """Load the sound, passing a position argument."""
        self.generator, self.source = play_path(
            ctx, self.sound_path, position=self.coordinates
        )
