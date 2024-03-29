"""Mapping functions and classes for Earwax.

This module is inspired by Camlorn's post at `this link
<https://forum.audiogames.net/post/565561/#p565561>`_.

All credit goes to him for the idea.
"""

from .box import Box, BoxBounds, BoxTypes, NotADoor, NotAPortal
from .box_level import BoxLevel, CurrentBox, NearestBox
from .door import Door
from .map_editor import MapEditor, MapEditorContext
from .portal import Portal

__all__ = [
    # box.py:
    "Box",
    "BoxBounds",
    "BoxTypes",
    "NotADoor",
    "NotAPortal",
    # box_level.py:
    "BoxLevel",
    "CurrentBox",
    "NearestBox",
    # door.py:
    "Door",
    # map_editor.py:
    "MapEditor",
    "MapEditorContext",
    # portal.py:
    "Portal",
]
