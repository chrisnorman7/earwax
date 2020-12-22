"""Provides the Track class."""

from enum import Enum
from typing import Optional

from attr import Factory, attrib, attrs

from .sound import Sound, SoundManager


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

    :ivar ~earwax.Track.sound_manager: sound manager to play sounds with.

        This value is initialised as part of the :meth:`~earwax.Track.play`
        method.

    :ivar ~earwax.Track.sound: The currently playing sound instance.

        This value is initialised as part of the :meth:`~earwax.Track.play`
        method.
    """

    protocol: str
    path: str
    track_type: TrackTypes

    sound_manager: Optional[SoundManager] = attrib(
        default=Factory(type(None)), init=False, repr=False
    )
    sound: Optional[Sound] = attrib(
        default=Factory(type(None)), init=False, repr=False
    )

    def play(self, manager: SoundManager) -> None:
        """Play this track on a loop.

        To alter how ``sound_path`` is played, override
        :meth:`earwax.Track.load_sound`.

        :param manager: The sound manager to play through.
        """
        self.sound_manager = manager
        self.sound = manager.play_stream(self.protocol, self.path)

    def stop(self) -> None:
        """Stop this track playing."""
        if self.sound_manager is not None:
            if self.sound is not None:
                self.sound_manager.destroy_sound(self.sound)
                self.sound = None
            self.sound_manager = None
