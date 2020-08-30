"""Mapping utilities for Earwax.

This module is inspired by Camlorn's post at `this link
<https://forum.audiogames.net/post/565561/#p565561>`__

All credit goes to him for the idea.
"""

from .box import Box, FittedBox, OutOfBounds, box_row
from .point import Point, PointDirections

__all__ = [
    'Box', 'Point', 'OutOfBounds', 'PointDirections', 'FittedBox', 'box_row'
]
