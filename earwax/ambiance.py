"""Provides the Ambiance class."""

from typing import Optional

from attr import Factory, attrib, attrs

try:
    from synthizer import Context, Source3D
except ModuleNotFoundError:
    Context, Source3d = (None, None)

from .point import Point
from .sound import Sound, SoundManager


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

    :ivar ~earwax.Ambiance.sound_manager: The sound manager which this ambiance
        will play through.

        This value is initialised as part of the :meth:`~earwax.Ambiance.play`
        method.

    :ivar ~earwax.Ambiance.sound: The playing sound.

        This value is initialised as part of the :meth:`~earwax.Ambiance.play`
        method.
    """

    protocol: str
    path: str
    coordinates: Point = Point(0, 0, 0)
    sound_manager: Optional[SoundManager] = attrib(
        default=Factory(type(None)), init=False, repr=False
    )
    sound: Optional[Sound] = attrib(
        default=Factory(type(None)), init=False, repr=False
    )

    def play(self, ctx: Context) -> None:
        """Load and position the sound.

        :param ctx: The Synthizer context to use.
        """
        if self.sound_manager is None:
            self.sound_manager = SoundManager(
                ctx, Source3D(ctx), should_loop=True
            )
            self.set_position(self.coordinates)
        if self.sound is None:
            self.sound = self.sound_manager.play_stream(
                self.protocol, self.path
            )

    def stop(self) -> None:
        """Stop this ambiance playing."""
        if self.sound_manager is not None:
            self.sound_manager.destroy_all()
        self.sound = None

    def set_position(self, pos: Point) -> None:
        """Move this ambiance.

        This method should be used instead of setting :attr:`self.coordinates
        <earwax.Ambiance.coordinates>` directly, as this method will also
        update the position of :attr:`self.sound_manager
        <earwax.Ambiance.sound_manager>`'s source.

        :param pos: The new position.
        """
        self.coordinates = pos
        if self.sound_manager is not None:
            self.sound_manager.source.position = pos.coordinates
