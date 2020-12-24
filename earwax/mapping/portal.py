"""Provides the Portal class."""

from pathlib import Path
from typing import TYPE_CHECKING, Optional

from attr import attrs

from ..mixins import RegisterEventMixin
from ..point import Point

if TYPE_CHECKING:
    from .box_level import BoxLevel


@attrs(auto_attribs=True)
class Portal(RegisterEventMixin):
    """A portal to another map.

    An object that can be added to a :class:`earwax.Box` to make a link
    between two maps.

    This class implements ``pyglet.event.EventDispatcher``, so events can be
    registered and dispatched on it.

    The currently-registered events are:

        * :meth:`~earwax.Portal.on_enter`

        * :meth:`~earwax.Portal.on_exit`

    :ivar ~earwax.Portal.level: The destination level.

    :ivar ~earwax.Portal.coordinates: The exit coordinates.

    :ivar ~earwax.Portal.bearing: If this value is ``None``, then it will be
        used for the player's bearing after this portal is used. Otherwise, the
        bearing from the old level will be used.

    :ivar ~earwax.Portal.enter_sound: The sound that should play when entering
        this portal.

    :ivar ~earwax.Portal.exit_sound: The sound that should play when exiting
        this portal.
    """

    level: 'BoxLevel'
    coordinates: Point
    bearing: Optional[int] = None

    enter_sound: Optional[Path] = None
    exit_sound: Optional[Path] = None

    def __attrs_post_init__(self) -> None:
        """Register default events."""
        self.register_event_type('on_enter')
        self.register_event_type('on_exit')

    def on_enter(self) -> None:
        """Handle a player entering this portal."""
        pass

    def on_exit(self) -> None:
        """Handle a player exiting this portal."""
        pass
