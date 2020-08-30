"""Provides the walking_directions dictionary."""

from typing import Dict, Tuple

from .mapping.point import PointDirections

Direction = Tuple[int, int]

walking_directions: Dict[PointDirections, Direction] = {
    PointDirections.north: (0, 1),
    PointDirections.northeast: (1, 1),
    PointDirections.east: (1, 0),
    PointDirections.southeast: (1, -1),
    PointDirections.south: (0, -1),
    PointDirections.southwest: (-1, -1),
    PointDirections.west: (-1, 0),
    PointDirections.northwest: (-1, 1),
    PointDirections.here: (0, 0)
}
