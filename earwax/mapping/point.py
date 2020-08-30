"""Provides the Point class."""

from typing import Union

from attr import attrs


@attrs(auto_attribs=True)
class Point:
    """A point in 2d space."""

    x: int
    y: int

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
