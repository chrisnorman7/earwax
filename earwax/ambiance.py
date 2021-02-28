"""Provides the Ambiance class."""

from pathlib import Path
from typing import Optional

from attr import Factory, attrib, attrs

from .point import Point
from .sound import Sound, SoundManager
from .utils import random_file


@attrs(auto_attribs=True)
class Ambiance:
    """A class that represents a positioned sound on a map.

    If you want to know more about the ``stream`` and ``path`` attributes, see
    the documentation for ``synthizer.StreamingGenerator``.

    :ivar ~earwax.Track.protocol: The ``protocol`` argument to pass to
        ``synthizer.StreamingGenerator````.

    :ivar ~earwax.Track.path: The ``path`` argument to pass to
        ``synthizer.StreamingGenerator``.

    :ivar ~earwax.Ambiance.coordinates: The coordinates of this ambiance.

    :ivar ~earwax.Ambiance.sound: The playing sound.

        This value is initialised as part of the :meth:`~earwax.Ambiance.play`
        method.
    """

    protocol: str
    path: str
    coordinates: Point

    sound: Optional[Sound] = attrib(
        default=Factory(type(None)), init=False, repr=False
    )

    @classmethod
    def from_path(cls, path: Path, coordinates: Point) -> "Ambiance":
        """Return a new instance from a path.

        :param path: The path to build the ambiance from.

            If this value is a directory, then a random file will be chosen.

        :param coordinates: The coordinates of this ambiance.
        """
        path = random_file(path)
        return cls("file", str(path), coordinates=coordinates)

    def play(self, sound_manager: SoundManager, **kwargs) -> None:
        """Load and position the sound.

        :param sound_manager: The sound manager which will be used to play this
            ambiance.

        :param kwargs: The additional keyword arguments to pass to
            :meth:`~earwax.SoundManager.play_path`.
        """
        kwargs.setdefault("position", self.coordinates)
        kwargs.setdefault("looping", True)
        self.sound = sound_manager.play_stream(
            self.protocol, self.path, **kwargs
        )

    def stop(self) -> None:
        """Stop this ambiance from playing."""
        if self.sound is not None:
            self.sound.destroy()
            self.sound = None
