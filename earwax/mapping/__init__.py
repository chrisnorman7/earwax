"""Mapping utilities for Earwax.

This module is inspired by Camlorn's post at `this link
<https://forum.audiogames.net/post/565561/#p565561>`__

All credit goes to him for the idea.
"""

from .box import (Box, BoxBounds, BoxSound, BoxTypes, NotADoor, OutOfBounds,
                  box_row)
from .box_level import BoxLevel
from .door import Door
from .portal import Portal

__all__ = [
    'Box', 'OutOfBounds', 'BoxTypes', 'box_row', 'BoxLevel', 'Door',
    'NotADoor', 'Portal', 'BoxBounds', 'BoxSound'
]
