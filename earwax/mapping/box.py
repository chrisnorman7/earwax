"""Provides the Box class."""

from typing import List, Optional

from attr import Factory, attrs

from .point import Point


class OutOfBounds(Exception):
    """The given point is beyond the bounds of a box."""


@attrs(auto_attribs=True)
class Box:
    """A box on a map."""

    bottom_left: Point
    top_right: Optional[Point] = None
    name: Optional[str] = None
    description: Optional[str] = None
    parent: Optional['Box'] = None
    children: List['Box'] = Factory(list)

    def __attrs_post_init__(self) -> None:
        if self.top_right is None:
            self.top_right = Point(self.bottom_left.x, self.bottom_left.y)

    @property
    def top_left(self) -> Point:
        """Returns the coordinates of the top left corner of this box."""
        return Point(
            self.bottom_left.x,
            self.bottom_left.y if self.top_right is None else self.top_right.y
        )

    @property
    def bottom_right(self) -> Point:
        """Returns the coordinates of the bottom right corner of this box."""
        return Point(
            self.bottom_left.x if self.top_right is None else self.top_right.x,
            self.bottom_left.y)

    def add_child(self, box: 'Box') -> None:
        """Adds the given box to :attr:`self.children
        <~earwax.Box.children>`.

        :param box: The box to add as a child.
        """
        if box.bottom_left < self.bottom_left or (
            box.bottom_left if box.top_right is None else box.top_right
        ) > (
            self.bottom_left if self.top_right is None else self.top_right
        ):
            raise OutOfBounds(self, box)
        self.children.append(box)
        box.parent = self
