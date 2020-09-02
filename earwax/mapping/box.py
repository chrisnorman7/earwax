"""Provides box-related classes, functions, and exceptions."""

from pathlib import Path
from typing import List, Optional

from attr import Factory, attrib, attrs
from pyglet.event import EventDispatcher
from synthizer import Context

from ..sound import play_path
from .door import Door
from .point import Point


class BoxError(Exception):
    """The base exception for all box errors."""


class OutOfBounds(BoxError):
    """The given point is beyond the bounds of a box."""


class NotADoor(BoxError):
    """Tried to call :meth:`~earwax.Box.open`, or :meth:`~earwax.Box.close`
    on a :class:`~earwax.Box` instance that has its :attr:`~earwax.Box.door`
    attribute set to ``None``."""


@attrs(auto_attribs=True)
class Box(EventDispatcher):
    """A box on a map.

    You can create instances of this class either singly, or by using the
    :meth:`earwax.box_row` method.

    In addition to the coordinates supplied to this class's constructor,
    properties are also generated for :attr:`~earwax.Box.rop_left`, and
    :attr:`~earwax.Box.bottom_right`.

    This class uses the `pyglet.event
    <https://pyglet.readthedocs.io/en/latest/modules/event.html>`__ framework,
    so you can register and dispatch events in the same way you would with
    ``pyglet.window.Window``, or any other ``EventDispatcher`` subclass.

    :ivar ~earwax.Box.bottom_left: The coordinates at the bottom left corner of
        this box.

    :ivar ~earwax.Box.top_right: The coordinates at the top right corner of
        this box.

    :ivar ~earwax.Box.name: An optional name for this box.

    :ivar ~earwax.Box.parent: The box that contains this one.

        If you supply a ``parent`` argument to the constructor, this box will
        be added to the :attr:`~earwax.Box.children` attribute of the parent.

    :ivar ~earwax.Box.children: A list of boxes that are contained by this box.

        To add a child, use the :meth:`~earwax.Box.add_child` method.

    :ivar ~earwax.Box.wall: A flag to specify whether or not this instance is a
        wall.

    :ivar ~earwax.Box.door: If this attribute is not ``None``, then this
        instance is considered a door.

    :ivar ~earwax.Box.surface_sound: A path to either the sound that should be
        heard when a player enters this box, or the path of a directory from
        which a random file should be chosen.

    :ivar ~earwax.Box.wall_sound: A path to either the sound that should be
        heard when a player collides with this box, or the path of a directory
        from which a random file should be chosen.
    """

    bottom_left: Point
    top_right: Point

    name: Optional[str] = None

    parent: Optional['Box'] = None
    children: List['Box'] = attrib(Factory(list), repr=False)

    wall: bool = False
    door: Optional[Door] = None

    surface_sound: Optional[Path] = None
    wall_sound: Optional[Path] = None

    def __attrs_post_init__(self) -> None:
        if self.parent is not None:
            self.parent.add_child(self)
        child: Box
        for child in self.children:
            child.parent = self
        self.register_event_type('on_footstep')
        self.register_event_type('on_collide')
        self.register_event_type('on_activate')
        self.register_event_type('on_open')
        self.register_event_type('on_close')

    def on_footstep(self) -> None:
        """Play an appropriate surface sound.

        This function will be called by the Pyglet event framework, and should
        be called when a player is walking on this box."""
        pass

    def on_collide(self) -> None:
        """Play an appropriate wall sound.

        This function will be called by the Pyglet event framework, and should
        be called when a player collides with this box.
        """
        pass

    def on_activate(self) -> None:
        """An event which is dispatched when the player presses the enter key.

        It is guaranteed that the instance this event is dispatched on is the
        one the player is stood on.
        """
        pass

    def on_open(self) -> None:
        """An event that id dispatched when the :meth:`~earwax.Box.open` method is
        successfully called on this instance."""
        pass

    def on_close(self) -> None:
        """An event which is dispatched when :meth:`~earwax.Box.close` is
        successfully called on this instance."""
        pass

    @property
    def top_left(self) -> Point:
        """Returns the coordinates of the top left corner of this box."""
        return Point(self.bottom_left.x, self.top_right.y)

    @property
    def bottom_right(self) -> Point:
        """Returns the coordinates of the bottom right corner of this box."""
        return Point(self.top_right.x, self.bottom_left.y)

    @property
    def width(self) -> int:
        """Returns the width of this box."""
        return self.bottom_right.x - self.bottom_left.x

    @property
    def height(self) -> int:
        """Returns the height of this box."""
        return self.top_left.y - self.bottom_left.y

    @property
    def area(self) -> int:
        """Returns the area of the box."""
        return self.width * self.height

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

    def sort_children(self) -> List['Box']:
        """Returns a sorted version of :attr:`~earwax.Box.children`."""
        return sorted(self.children, key=lambda c: c.area)

    def get_containing_box(self, coordinates: Point) -> Optional['Box']:
        """Returns the box that spans the given coordinates.

        If no child box is found, one of two things will occur:

        * If ``self`` contains the given coordinates, ``self`` will be
            returned.

        * If that is not the case, `None`` is returned.

        This method scans :attr:`self.children <earwax.Box.children>` using the
        :meth:`~earwax.Box.sort_children` method..

        :param coordinates: The coordinates the child box should span.
        """
        box: Box
        for box in self.sort_children():
            if box.contains_point(coordinates):
                return box
        if self.contains_point(coordinates):
            return self
        return None

    def open(self, ctx: Optional[Context]) -> None:
        """If :attr:`self.door <earwax.Box.door>` is not ``None``, set its
        :attr:`.open <earwax.Door.open>` attribute to ``True``, and play the
        appropriate sound. Otherwise, raise :class:`earwax.NotADoor`."""
        if self.door is None:
            raise NotADoor(self)
        self.door.open = True
        self.dispatch_event('on_open')
        if self.door.open_sound is not None and ctx is not None:
            play_path(ctx, self.door.open_sound, position=(self.bottom_left.x, self.bottom_left.y, 0.0))

    def close(self, ctx: Optional[Context]) -> None:
        """If :attr:`self.door <earwax.Box.door>` is not ``None``, set its
        :attr:`.open <earwax.Door.open>` attribute to ``False``, and play the
        appropriate sound. Otherwise, raise :class:`earwax.NotADoor`."""
        if self.door is None:
            raise NotADoor(self)
        self.door.open = False
        self.dispatch_event('on_close')
        if self.door.close_sound is not None and ctx is not None:
            play_path(ctx, self.door.close_sound)


class FittedBox(Box):
    """A box that fits all its children in.

    Pass a list of :class:`~earwax.Box` instances, and you'll get a box with
    its :attr:`~earwax.Box.bottom_left`, and :attr:`~earwax.Box.top_right`
    attributes set to match the outer bounds of the provided children."""

    def __init__(self, children: List[Box], **kwargs) -> None:
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
                Point(top_right_x, top_right_y),
                children=children, **kwargs
            )
        else:
            raise ValueError('Invalid children: %r.' % children)


def box_row(
    start: Point, x_size: int, y_size: int, count: int, x_offset: int,
    y_offset: int, **kwargs
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

    This will result in a list containing 3 rooms:

    * The first from (0, 0) to (2, 1)

    * The second from (3, 0) to (5, 1)

    * And the third from (6, 0) to (8, 1)

    **PLEASE NOTE:**
    If the value of either of the size arguments is less than 1, the top right
    coordinate will be less than the bottom left, so
    :meth:`~earwax.Box.get_containing_box` won't ever find it.

    :param start: The :attr:`~earwax.Box.bottom_left` coordinate of the first
        box.

    :param x_size: The width of each box.

    :param y_size: The depth of each box.

    :param count: The number of boxes to build.

    :param x_offset: The amount of x distance between the boxes.

        If the provided value is less than 1, then overlaps will occur.

    :param y_offset: The amount of y distance between the boxes.

        If the provided value is less than 1, then overlaps will occur.

    :param kwargs: Extra keyword arguments to be passed to ``Box.__init__``.
    """
    start = start.copy()
    # In the next line, we subtract 1 from both size values, otherwise we end
    # up with a box that is too large by 1 on each axis.
    size_point: Point = Point(x_size - 1, y_size - 1)
    n: int
    boxes: List[Box] = []
    for n in range(count):
        box: Box = Box(start.copy(), start + size_point, **kwargs)
        boxes.append(box)
        if x_offset:
            start.x += ((x_offset + x_size) - 1)
        if y_offset:
            start.y += ((y_offset + y_size) - 1)
    return boxes
