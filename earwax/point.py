"""Provides the Point class."""

from enum import Enum
from math import dist, floor
from typing import Any, Generic, Tuple, Type, TypeVar, Union, cast

from attr import attrs
from movement_2d import angle_between, coordinates_in_direction

T = TypeVar('T', float, int)


class PointDirections(Enum):
    """Point directions enumeration.

    Most of the possible directions between two :class:`~earwax.Point`
    instances.

    There are no vertical directions defined, although they would be easy to
    include.
    """

    here = 0
    north = 1
    northeast = 2
    east = 3
    southeast = 4
    south = 5
    southwest = 6
    west = 7
    northwest = 8


@attrs(auto_attribs=True, order=False, hash=True)
class Point(Generic[T]):
    """A point in 3d space."""

    x: T
    y: T
    z: T

    @classmethod
    def origin(cls) -> 'Point[int]':
        """Return ``Point(0, 0, 0)``."""
        return cast(Type[Point[int]], cls)(0, 0, 0)

    @property
    def coordinates(self) -> Tuple[T, T, T]:
        """Return ``self.x``, ``self.y``, and ``self.z`` as a tuple."""
        return self.x, self.y, self.z

    def directions_to(self, other: 'Point') -> PointDirections:
        """Return the direction between this point and ``other``.

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

    def distance_between(self, other: 'Point') -> float:
        """Return the distance between two points.

        :param other: The point to measure the distance to.
        """
        return dist(self.coordinates, other.coordinates)

    def angle_between(self, other: 'Point') -> float:
        """Return the angle between two points.

        :param other: The other point to get the angle to.
        """
        x1: float
        y1: float
        z1: float
        x2: float
        y2: float
        z2: float
        x1, y1, z1 = self.coordinates
        x2, y2, z2 = other.coordinates
        return angle_between(x1, y1, x2, y2)

    def in_direction(
        self, angle: float, distance: float = 1.0
    ) -> 'Point[float]':
        """Return the coordinates in the given direction.

        :param angle: The direction of travel.

        :param distance: The distance to travel.
        """
        x: float
        y: float
        x, y = coordinates_in_direction(
            self.x, self.y, angle, distance=distance
        )
        return Point(x, y, float(self.z))

    def copy(self) -> 'Point[T]':
        """Copy this instance.

        Returns a ``Point`` instance with duplicate ``x`` and ``y``
        values.
        """
        return type(self)(self.x, self.y, self.z)

    def floor(self) -> 'Point[int]':
        """Return a version of this object with both coordinates floored."""
        return cast(Type[Point[int]], type(self))(
            floor(self.x), floor(self.y), floor(self.z)
        )

    def __add__(self, offset: Union[int, 'Point']) -> 'Point':
        """Add two points together."""
        if isinstance(offset, int):
            return Point(self.x + offset, self.y + offset, self.z + offset)
        elif isinstance(offset, Point):
            return Point(
                self.x + offset.x, self.y + offset.y, self.z + offset.z
            )
        else:
            raise TypeError(
                'Invalid type for offset: Expected an int or a Point '
                f'instance. Got {type(offset)} instead.'
            )

    def __sub__(self, offset: Union[int, 'Point']) -> 'Point':
        """Subtract two points."""
        if isinstance(offset, int):
            return Point(self.x - offset, self.y - offset, self.z - offset)
        elif isinstance(offset, Point):
            return Point(
                self.x - offset.x, self.y - offset.y, self.z - offset.z
            )
        else:
            raise TypeError(
                'Invalid type for offset: Expected an int or a Point '
                f'instance. Got {type(offset)} instead.'
            )

    def __mul__(self, offset: Union[int, 'Point']) -> 'Point':
        """Multiply two points."""
        if isinstance(offset, int):
            return Point(self.x * offset, self.y * offset, self.z * offset)
        elif isinstance(offset, Point):
            return Point(
                self.x * offset.x, self.y * offset.y, self.z * offset.z
            )
        else:
            raise TypeError(
                'Invalid type for offset: Expected an int or a Point '
                f'instance. Got {type(offset)} instead.'
            )

    def __neg__(self) -> 'Point':
        """Return a negative version of this instance.

        Returns a copy of this instance with all its coordinates multiplied
        by -1.
        """
        cls = type(self)
        return cls(self.x * -1, self.y * -1, self.z * -1)

    def __eq__(self, other: Any) -> bool:
        """Equality test."""
        if other.__class__ is self.__class__:
            return (
                other.x == self.x and other.y == self.y and other.z == self.z
            )
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        """Not equal."""
        if other.__class__ is self.__class__:
            return (
                other.x != self.x and other.y != self.y and other.z != self.z
            )
        return NotImplemented

    def __lt__(self, other: Any) -> bool:
        """Less than."""
        if other.__class__ is self.__class__:
            return self.x < other.x and self.y < other.y and self.z < other.z
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        """Greater than."""
        if other.__class__ is self.__class__:
            return self.x > other.x and self.y > other.y and self.z > other.z
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        """Lessthan or equal to."""
        return self < other or self == other

    def __ge__(self, other: Any) -> bool:
        """Greaterthan or equal to."""
        return self > other or self == other
