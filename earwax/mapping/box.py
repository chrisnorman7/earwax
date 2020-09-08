"""Provides box-related classes, functions, and exceptions."""

from pathlib import Path
from random import uniform
from typing import List, Optional

from attr import Factory, attrib, attrs
from pyglet.clock import schedule_once, unschedule
from pyglet.event import EventDispatcher
from synthizer import Context

from ..point import Point
from ..sound import play_and_destroy
from .door import Door
from .portal import Portal


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

    :ivar ~earwax.Box.portal: If this attribute is not ``None``, then this
        instance is considered a portal.

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
    portal: Optional[Portal] = None

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
    def width(self) -> float:
        """Returns the width of this box."""
        return self.top_right.x - self.bottom_left.x

    @property
    def depth(self) -> float:
        """Get the depth of this box (front to back)."""
        return self.top_right.y - self.bottom_left.y

    @property
    def height(self) -> float:
        """Returns the height of this box."""
        return self.top_right.z - self.bottom_left.z

    @property
    def area(self) -> float:
        """Returns the area of the box."""
        return self.width * self.depth

    @property
    def volume(self) -> float:
        """Return the volume of this box."""
        return self.width * self.depth * self.height

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
                coordinates.z >= self.bottom_left.z,
                coordinates.x <= self.top_right.x,
                coordinates.y <= self.top_right.y,
                coordinates.z <= self.top_right.z
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

    def play_sound(self, ctx: Optional[Context], path: Optional[Path]) -> None:
        """Play a sound at the same position as this box.

        :param ctx: The ``synthizer.Context`` instance to play the sound
            through. If this value is ``None``, this method does nothing.

        :param path: A path to play. Can be None, in which case this method
            does nothing.
        """
        if ctx is not None and path is not None:
            play_and_destroy(
                ctx, path,
                position=(self.bottom_left.x, self.bottom_left.y, 0.0)
            )

    def open(self, ctx: Optional[Context]) -> None:
        """If :attr:`self.door <earwax.Box.door>` is not ``None``, set its
        :attr:`.open <earwax.Door.open>` attribute to ``True``, and play the
        appropriate sound. Otherwise, raise :class:`earwax.NotADoor`."""
        if self.door is None:
            raise NotADoor(self)
        self.door.open = True
        self.dispatch_event('on_open')
        self.play_sound(ctx, self.door.open_sound)
        when: float
        if isinstance(self.door.close_after, tuple):
            when = uniform(*self.door.close_after)
        elif isinstance(self.door.close_after, float):
            when = self.door.close_after
        else:
            return None
        schedule_once(self.scheduled_close, when, ctx)

    def close(self, ctx: Optional[Context]) -> None:
        """If :attr:`self.door <earwax.Box.door>` is not ``None``, set its
        :attr:`.open <earwax.Door.open>` attribute to ``False``, and play the
        appropriate sound. Otherwise, raise :class:`earwax.NotADoor`.
        """
        unschedule(self.scheduled_close)
        if self.door is None:
            raise NotADoor(self)
        self.door.open = False
        self.dispatch_event('on_close')
        self.play_sound(ctx, self.door.close_sound)

    def scheduled_close(self, dt: float, ctx: Optional[Context]) -> None:
        """Call :meth:`self.close() <earwax.Box.close>` on a schedule."""
        self.close(ctx)


class FittedBox(Box):
    """A box that fits all its children in.

    Pass a list of :class:`~earwax.Box` instances, and you'll get a box with
    its :attr:`~earwax.Box.bottom_left`, and :attr:`~earwax.Box.top_right`
    attributes set to match the outer bounds of the provided children."""

    def __init__(self, children: List[Box], **kwargs) -> None:
        """Create a new instance."""
        bottom_left_x: Optional[float] = None
        bottom_left_y: Optional[float] = None
        bottom_left_z: Optional[float] = None
        top_right_x: Optional[float] = None
        top_right_y: Optional[float] = None
        top_right_z: Optional[float] = None
        child: Box
        for child in children:
            if bottom_left_x is None or child.bottom_left.x < bottom_left_x:
                bottom_left_x = child.bottom_left.x
            if bottom_left_y is None or child.bottom_left.y < bottom_left_y:
                bottom_left_y = child.bottom_left.y
            if bottom_left_z is None or child.bottom_left.z < bottom_left_z:
                bottom_left_z = child.bottom_left.z
            if top_right_x is None or child.top_right.x > top_right_x:
                top_right_x = child.top_right.x
            if top_right_y is None or child.top_right.y > top_right_y:
                top_right_y = child.top_right.y
            if top_right_z is None or child.top_right.z > top_right_z:
                top_right_z = child.top_right.z
        if (
            bottom_left_x is not None and bottom_left_y is not None and
            bottom_left_z is not None and top_right_x is not None and
            top_right_y is not None and top_right_z is not None
        ):
            super().__init__(
                Point(bottom_left_x, bottom_left_y, bottom_left_z),
                Point(top_right_x, top_right_y, top_right_z),
                children=children, **kwargs
            )
        else:
            raise ValueError('Invalid children: %r.' % children)


def box_row(
    start: Point, size: Point, count: int, offset: Point, **kwargs
) -> List[Box]:
    """Generates a list of boxes.

    This method is useful for creating rows of buildings, or rooms on a
    corridor to name a couple of examples.

    It can be used like so::

        offices = row(
            Point(0, 0),  # The bottom_left corner of the first box.
            Point(3, 2, 0),  # The size of each box.
            3,  # The number of boxes to build.
            # The next argument is how far to move from the top right corner of
            # each created box:
            Point(1, 0, 0)
        )

    This will result in a list containing 3 rooms:

    * The first from (0, 0, 0) to (2, 1, 0)

    * The second from (3, 0, 0) to (5, 1, 0)

    * And the third from (6, 0, 0) to (8, 1, 0)

    **PLEASE NOTE:**
    If none of the size coordinates are ``>= 1``, the top right coordinate will
    be less than the bottom left, so :meth:`~earwax.Box.get_containing_box`
    won't ever find it.

    :param start: The :attr:`~earwax.Box.bottom_left` coordinate of the first
        box.

    :param size: The size of each box.

    :param count: The number of boxes to build.

    :param offset: The distance between the boxes.

        If no coordinate of the given value is ``>= 1``, overlaps will occur.

    :param kwargs: Extra keyword arguments to be passed to ``Box.__init__``.
    """
    start = start.copy()
    # In the next line, we subtract 1 from all size values, otherwise we end up
    # with a box that is too large by 1 on each axis.
    size -= 1
    boxes: List[Box] = []
    n: int = 0
    while n < count:
        box: Box = Box(start.copy(), start + size, **kwargs)
        boxes.append(box)
        if offset.x:
            start.x += offset.x + size.x
        if offset.y:
            start.y += offset.y + size.y
        if offset.z:
            start.z += offset.z + size.z
        n += 1
    return boxes
