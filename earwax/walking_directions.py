"""Provides the walking_directions dictionary."""

from typing import Dict

from .point import Point, PointDirections

walking_directions: Dict[PointDirections, Point] = {
    PointDirections.north: Point(0, 1, 0),
    PointDirections.northeast: Point(1, 1, 0),
    PointDirections.east: Point(1, 0, 0),
    PointDirections.southeast: Point(1, -1, 0),
    PointDirections.south: Point(0, -1, 0),
    PointDirections.southwest: Point(-1, -1, 0),
    PointDirections.west: Point(-1, 0, 0),
    PointDirections.northwest: Point(-1, 1, 0),
    PointDirections.here: Point(0, 0, 0)
}
