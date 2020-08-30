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
    top_right: Point
    name: Optional[str] = None
    parent: Optional['Box'] = None
    children: List['Box'] = Factory(list)

    def __attrs_post_init__(self) -> None:
        if self.parent is not None:
            self.parent.add_child(self)

    @property
    def top_left(self) -> Point:
        """Returns the coordinates of the top left corner of this box."""
        return Point(self.bottom_left.x, self.top_right.y)

    @property
    def bottom_right(self) -> Point:
        """Returns the coordinates of the bottom right corner of this box."""
        return Point(self.top_right.x, self.bottom_left.y)

    def add_child(self, box: 'Box') -> None:
        """Adds the given box to :attr:`self.children
        <~earwax.Box.children>`.

        :param box: The box to add as a child.
        """
        if not self.could_fit(box):
            raise OutOfBounds(self, box)
        self.children.append(box)
        box.parent = self

    def contains_point(self, coordinates: Point) -> bool:
        """Returns ``True`` if this box spans the given coordinates, ``False``
        otherwise.

        :param coordinates: The coordinates to check.
        """
        return all(
            (
                coordinates.x >= self.bottom_left.x,
                coordinates.y >= self.bottom_left.y,
                coordinates.x <= self.top_right.x,
                coordinates.y <= self.top_right.y
            )
        )

    def could_fit(self, box: 'Box') -> bool:
        """Returns ``True`` if the given box could be contained by this box,
        ``False`` otherwise.

        This method behaves like the :meth:`~earwax.Box.contains_point` method,
        except that it works with :class:`~earwax.Box` instances, rather than
        :class:`~earwax.Point` instances.

        This method doesn't care about the :attr:`~earwax.Box.parent` attribute
        on the given box. This method simply checks that the
        :attr:`~earwax.Box.bottom_left` and :attr:`~earwax.Box.top_right`
        points would fit inside this box.

        :param box: The box whose bounds will be checked.
        """
        return self.contains_point(
            box.bottom_left
        ) and self.contains_point(
            box.top_right
        )

    def get_containing_box(self, coordinates: Point) -> Optional['Box']:
        """Returns the box that spans the given coordinates.

        If no child box is found, one of two things will occur:

        * If ``self`` contains the given coordinates, ``self`` will be
        returned.

        * If that is not the case, `None`` is returned.
        This method scans :attr:`self.children <earwax.Box.children>`.

        :param coordinates: The coordinates the child box should span.
        """
        box: Box
        for box in self.children:
            if box.contains_point(coordinates):
                return box
        if self.contains_point(coordinates):
            return self
        return None
