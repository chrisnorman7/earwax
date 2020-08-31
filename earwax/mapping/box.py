"""Provides box-related classes, functions, and exceptions."""

from typing import List, Optional

from attr import Factory, attrib, attrs

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
    children: List['Box'] = attrib(Factory(list), repr=False)

    def __attrs_post_init__(self) -> None:
        if self.parent is not None:
            self.parent.add_child(self)
        child: Box
        for child in self.children:
            child.parent = self

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


class FittedBox(Box):
    """A box that fits all its children in.

    Pass a list of :class:`~earwax.Box` instances, and you'll get a box with
    its :attr:`~earwax.Box.bottom_left`, and :attr:`~earwax.Box.top_right`
    attributes set to match the outer bounds of the provided children."""

    def __init__(self, children: List[Box]) -> None:
        """Create a new instance."""
        bottom_left_x: Optional[int] = None
        bottom_left_y: Optional[int] = None
        top_right_x: Optional[int] = None
        top_right_y: Optional[int] = None
        child: Box
        for child in children:
            if bottom_left_x is None or child.bottom_left.x < bottom_left_x:
                bottom_left_x = child.bottom_left.x
            if bottom_left_y is None or child.bottom_left.y < bottom_left_y:
                bottom_left_y = child.bottom_left.y
            if top_right_x is None or child.top_right.x > top_right_x:
                top_right_x = child.top_right.x
            if top_right_y is None or child.top_right.y > top_right_y:
                top_right_y = child.top_right.y
        if bottom_left_x is not None and bottom_left_y is not None and \
           top_right_x is not None and top_right_y is not None:
            super().__init__(
                Point(bottom_left_x, bottom_left_y),
                Point(top_right_x, top_right_y), children=children
            )
        else:
            raise ValueError('Invalid children: %r.' % children)


def box_row(
    start: Point, x_size: int, y_size: int, count: int, x_offset: int,
    y_offset: int
) -> List[Box]:
    """Generates a list of boxes.

    This method is useful for creating rows of buildings, or rooms on a
    corridor to name a couple of examples.

    It can be used like so::

        offices = row(
            Point(0, 0),  # The bottom_left corner of the first box.
            3,  # The width (x) of each box.
            2,  # The depth (y) of each box.
            3,  # The number of boxes to build.
            1  # How far to travel along the x axis each time.
            0  # How far to travel on the y axis each time.
        )

    This will result a list containing 3 rooms:

    * The first from (0, 0) to (2, 1)

    * The second from (3, 0) to (5, 1)

    * And the third from (6, 0) to (8, 1)

    :param start: The :attr:`~earwax.Box.bottom_left` coordinate of the first
        box.

    :param x_size: The width of each box.

    :param y_size: The depth of each box.

    :param count: The number of boxes to build.

    :param x_offset: The amount of x distance between the boxes.

        If the provided value is less than 1, then overlaps will occur.

    :param y_offset: The amount of y distance between the boxes.

        If the provided value is less than 1, then overlaps will occur.
    """
    start = start.copy()
    # In the next line, we subtract 1 from both size values, otherwise we end
    # up with a box that is too large by 1 on each axis.
    size_point: Point = Point(x_size - 1, y_size - 1)
    n: int
    boxes: List[Box] = []
    for n in range(count):
        box: Box = Box(start.copy(), start + size_point)
        boxes.append(box)
        if x_offset:
            start.x += ((x_offset + x_size) - 1)
        if y_offset:
            start.y += ((y_offset + y_size) - 1)
    return boxes