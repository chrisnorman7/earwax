"""Provides the Door class."""

from pathlib import Path
from typing import Callable, Optional, Tuple, Union

from attr import attrs


@attrs(auto_attribs=True)
class Door:
    """An object that can be added to a box to optionally block travel.

    Doors can currently either be open or closed. When opened, they can
    optionally close after a specified time::

        Door()  # Standard open door.
        Door(open=False)  # Closed door.
        Door(close_after=5.0)  # Will automatically close after 5 seconds.
        # A door that will automatically close between 5 and 10 seconds after
        # it has been opened:
        Door(close_after=(5.0, 10.0)

    :ivar ~earwax.Door.open: Whether or not this box can be walked on.

        If this value is ``False``, then the player will hear
        :attr:`~earwax.Door.closed_sound` when trying to walk on this box.

        If this value is ``True``, the player will be able to enter the box as
        normal.

    :ivar ~earwax.Door.closed_sound: The sound that will be heard if
        :attr:`~earwax.Door.open` is ``False``.

    :ivar ~earwax.Door.open_sound: The sound that will be heard when opening
        this door.

    :ivar ~earwax.Door.close_sound: The sound that will be heard when closing
        this door.

    :ivar ~earwax.Door.close_after: When (if ever) to close the door after it
        has been opened.

        This attribute supports 3 possible values:

        * ``None``: The door will not close on its own.

        * A tuple of two positive floats ``a`` and ``b``: A random number
            between ``a`` and ``b`` will be selected, and the door will
            automatically close after that time.

        * A float: The exact time the door will automatically close after.

    :ivar ~earwax.Door.can_open: An optional method which will be used to
        decide whether or not this door can be opened at this time.

        This method must return ``True`` or ``False``, and must handle any
        messages which should be sent to the player.

    :ivar ~earwax.Door.can_close: An optional method which will be used to
        decide whether or not this door can be closed at this time.

        This method must return ``True`` or ``False``, and must handle any
        messages which should be sent to the player.
    """

    open: bool = True
    closed_sound: Optional[Path] = None
    open_sound: Optional[Path] = None
    close_sound: Optional[Path] = None
    close_after: Optional[Union[float, Tuple[float, float]]] = None
    can_open: Optional[Callable[[], bool]] = None
    can_close: Optional[Callable[[], bool]] = None
