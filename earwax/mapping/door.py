"""Provides the Door class."""

from pathlib import Path
from typing import Optional

from attr import attrs


@attrs(auto_attribs=True)
class Door:
    """An object that can be added to a box to optionally block travel.

    :ivar ~earwax.Door.open: Whether or not this box can be walked on.

        If this value is ``False``, then the player will hear
        :attr:`~earwax.Door.closed_sound`.

        If this value is ``True``, the player will be able to enter the box as
        normal.

    :ivar ~earwax.Door.closed_sound: The sound that will be heard if
        :attr:`~earwax.Door.open` is ``False``.

    :ivar ~earwax.Door.open_sound: The sound that will be heard when opening t
        is door.

    :ivar ~earwax.Door.close_sound: The sound that will be heard when closing
        this door.
    """

    open: bool = True
    closed_sound: Optional[Path] = None
    open_sound: Optional[Path] = None
    close_sound: Optional[Path] = None
