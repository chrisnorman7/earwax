"""Provides the Point class."""

from enum import Enum
from math import floor
from typing import Any, Union

from attr import attrs


class PointDirections(Enum):
    """All the possible directions between two :class:`~earwax.Point`
    instances."""

    here = 0
    north = 1
    northeast = 2
    east = 3
    southeast = 4
    south = 5
    southwest = 6
    west = 7
    northwest = 8


Number = Union[float, int]


@attrs(auto_attribs=True, order=False)
class Point:
    """A point in 2d space."""

    x: Number
    y: Number

    def directions_to(self, other: 'Point') -> PointDirections:
        """Returns the direction between this point and ``other``.

        :param other: The point to get directions to.
        """
        if other.x < self.x:
            if other.y < self.y:
                return PointDirections.southwest
            elif other.y == self.y:
                return PointDirections.west
            else:
                return PointDirections.northwest
        elif other.x > self.x:
            if other.y < self.y:
                return PointDirections.southeast
            elif other.y == self.y:
                return PointDirections.east
            else:
                return PointDirections.northeast
        elif other.y < self.y:
            return PointDirections.south
        elif other.y > self.y:
            return PointDirections.north
        else:
            return PointDirections.here

    def copy(self) -> 'Point':
        """Return a ``Point`` instance with duplicate ``x`` and ``y``
        values."""
        return type(self)(self.x, self.y)

    def floor(self) -> 'Point':
        """Return a version of this object with both coordinates floored."""
        return type(self)(floor(self.x), floor(self.y))

    def __add__(self, offset: Union[int, 'Point']) -> 'Point':
        """Add two points together."""
        if isinstance(offset, int):
            return Point(self.x + offset, self.y + offset)
        elif isinstance(offset, Point):
            return Point(self.x + offset.x, self.y + offset.y)
        else:
            raise TypeError(
                'Invalid type for offset: Expected an int or a Point '
                f'instance. Got {type(offset)} instead.'
            )

    def __sub__(self, offset: Union[int, 'Point']) -> 'Point':
        """Subtract two points."""
        if isinstance(offset, int):
            return Point(self.x - offset, self.y - offset)
        elif isinstance(offset, Point):
            return Point(self.x - offset.x, self.y - offset.y)
        else:
            raise TypeError(
                'Invalid type for offset: Expected an int or a Point '
                f'instance. Got {type(offset)} instead.'
            )

    def __mul__(self, offset: Union[int, 'Point']) -> 'Point':
        """Multiply two points."""
        if isinstance(offset, int):
            return Point(self.x * offset, self.y * offset)
        elif isinstance(offset, Point):
            return Point(self.x * offset.x, self.y * offset.y)
        else:
            raise TypeError(
                'Invalid type for offset: Expected an int or a Point '
                f'instance. Got {type(offset)} instead.'
            )

    def __eq__(self, other: Any) -> bool:
        """Equality test."""
        if other.__class__ is self.__class__:
            return other.x == self.x and other.y == self.y
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        """Not equal."""
        if other.__class__ is self.__class__:
            return other.x != self.x and other.y != self.y
        return NotImplemented

    def __lt__(self, other: Any) -> bool:
        """Less than."""
        if other.__class__ is self.__class__:
            return self.x < other.x and self.y < other.y
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        """Greater than."""
        if other.__class__ is self.__class__:
            return self.x > other.x and self.y > other.y
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        """Lessthan or equal to."""
        return self < other or self == other

    def __ge__(self, other: Any) -> bool:
        """Greaterthan or equal to."""
        return self > other or self == other
