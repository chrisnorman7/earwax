"""Provides the Track class."""

from enum import Enum
from pathlib import Path
from typing import Optional

from attr import Factory, attrib, attrs

from .sound import Sound, SoundManager
from .utils import random_file


class TrackTypes(Enum):
    """The type of a :class:`~earwax.Track` instance.

    :ivar ~earwax.TrackTypes.ambiance: An ambiance which will never moved, such
        as the background sound for a map.

        This type should not be confused with the :class:`earwax.Ambiance`
        class, which describes an ambiance which can be moved around the sound
        field.

    :ivar ~earwax.TrackTypes.music: A piece of background music.
    """

    ambiance = 0
    music = 1


@attrs(auto_attribs=True)
class Track:
    """A looping sound or piece of music.

    A track that plays while a :class:`earwax.Level` object is top of the
    levels stack.

    :ivar ~earwax.Track.protocol: The ``protocol`` argument to pass to
        ``synthizer.StreamingGenerator````.

    :ivar ~earwax.Track.path: The ``path`` argument to pass to
        ``synthizer.StreamingGenerator``.

    :ivar ~earwax.Track.track_type: The type of this track.

        This value determines which sound manager an instance will be connected
        to.

    :ivar ~earwax.Track.sound: The currently playing sound instance.

        This value is initialised as part of the :meth:`~earwax.Track.play`
        method.
    """

    protocol: str
    path: str
    track_type: TrackTypes

    sound: Optional[Sound] = attrib(
        default=Factory(type(None)), init=False, repr=False
    )

    @classmethod
    def from_path(cls, path: Path, type: TrackTypes) -> "Track":
        """Return a new instance from a path.

        :param path: The path to build the track from.

            If this value is a directory, a random file will be selected.

        :param type: The type of the new track.
        """
        path = random_file(path)
        return cls("file", str(path), type)

    def play(self, manager: SoundManager, **kwargs) -> None:
        """Play this track on a loop.

        :param manager: The sound manager to play through.

        :param kwargs: The extra keyword arguments to send to the given
            manager's :meth:`~earwax.SoundManager.play_stream` method.
        """
        kwargs.setdefault("looping", True)
        self.sound = manager.play_stream(self.protocol, self.path, **kwargs)

    def stop(self) -> None:
        """Stop this track playing."""
        if self.sound is not None:
            self.sound.destroy()
            self.sound = None
