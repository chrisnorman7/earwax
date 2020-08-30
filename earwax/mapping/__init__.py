"""Mapping utilities for Earwax.

This module is inspired by Camlorn's post at `this link
<https://forum.audiogames.net/post/565561/#p565561>`__

All credit goes to him for the idea.
"""

from .box import Box, OutOfBounds
from .point import Point

__all__ = ['Box', 'Point', 'OutOfBounds']
