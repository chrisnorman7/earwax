"""Provides box-related classes, functions, and exceptions."""

from enum import Enum
from pathlib import Path
from random import uniform
from typing import (TYPE_CHECKING, Any, Callable, Dict, Generic, List,
                    Optional, Tuple, TypeVar, cast)

from attr import Factory, attrib, attrs

from ..pyglet import schedule_once, unschedule

try:
    from synthizer import GlobalFdnReverb
except ModuleNotFoundError:
    GlobalFdnReverb = object

from ..mixins import RegisterEventMixin
from ..point import Point
from ..sound import SoundManager
from ..types import EventType
from .door import Door
from .portal import Portal

if TYPE_CHECKING:
    from ..game import Game
    from .box_level import BoxLevel

IntCoordinates = Tuple[int, int, int]
T = TypeVar('T')


class BoxError(Exception):
    """General box level error."""


class NotADoor(BoxError):
    """The current box is not a door."""


class NotAPortal(BoxError):
    """The current box is not a portal."""


class BoxTypes(Enum):
    """The type of a box.

    :ivar ~earwax.BoxTypes.empty: Empty space.

        Boxes of this type can be traversed wit no barriers.

    :ivar ~earwax.BoxTypes.room: An open room with walls around the edge.

        Boxes of this type can be entered by means of a door. The programmer
        must provide some means of exit.

    :ivar ~earwax.BoxTypes.solid: Signifies a solid, impassible barrier.

        Boxes of this type cannot be traversed.
    """

    empty = 0
    room = 1
    solid = 2


@attrs(auto_attribs=True)
class BoxBounds:
    """Bounds for a :class:`earwax.Box` instance.

    :ivar ~earwax.BoxBounds.bottom_back_left: The bottom back left point.

    :ivar ~earwax.BoxBounds.top_front_right: The top front right point.

    :ivar ~earwax.BoxBounds.bottom_front_left: The bottom front left point.

    :ivar ~earwax.BoxBounds.bottom_front_right: The bottom front right point.

    :ivar ~earwax.BoxBounds.bottom_back_right: The bottom back right point.

    :ivar ~earwax.BoxBounds.top_back_left: The top back left point.

    :ivar ~earwax.BoxBounds.top_front_left: The top front left point.

    :ivar ~earwax.BoxBounds.top_back_right: The top back right point.
    """

    bottom_back_left: Point
    top_front_right: Point
    bottom_front_left: Point = attrib(init=False, repr=False)
    bottom_front_right: Point = attrib(init=False, repr=False)
    bottom_back_right: Point = attrib(init=False, repr=False)
    top_back_left: Point = attrib(init=False, repr=False)
    top_front_left: Point = attrib(init=False, repr=False)
    top_back_right: Point = attrib(init=False, repr=False)

    def __attrs_post_init__(self) -> None:
        """Set all other points."""
        start_x: float
        start_y: float
        start_z: float
        end_x: float
        end_y: float
        end_z: float
        start_x, start_y, start_z = self.bottom_back_left.coordinates
        end_x, end_y, end_z = self.top_front_right.coordinates
        self.bottom_front_left = Point(start_x, end_y, start_z)
        self.bottom_front_right = Point(end_x, end_y, start_z)
        self.bottom_back_right = Point(end_x, start_y, start_z)
        self.top_back_left = Point(start_x, start_y, end_z)
        self.top_front_left = Point(start_x, end_y, end_z)
        self.top_back_right = Point(end_x, start_y, end_z)

    def is_edge(self, p: Point) -> bool:
        """Return ``True`` if ``p`` represents an edge.

        :param p: The point to interrogate.
        """
        x: int
        y: int
        z: int
        x, y, z = cast(IntCoordinates, p.floor().coordinates)
        start_x: int
        start_y: int
        start_z: int
        end_x: int
        end_y: int
        end_z: int
        start_x, start_y, start_z = cast(
            Tuple[int, int, int],
            self.bottom_back_left.floor().coordinates
        )
        end_x, end_y, end_z = cast(
            IntCoordinates, self.top_front_right.floor().coordinates
        )
        return (
            x == start_x or x == end_x or
            y == start_y or y == end_y or
            z == start_z or z == end_z
        )

    @property
    def width(self) -> float:
        """Return the width of this box."""
        return self.top_front_right.x - self.bottom_back_left.x

    @property
    def depth(self) -> float:
        """Get the depth of this box (front to back)."""
        return self.top_front_right.y - self.bottom_back_left.y

    @property
    def height(self) -> float:
        """Return the height of this box."""
        return self.top_front_right.z - self.bottom_back_left.z

    @property
    def area(self) -> float:
        """Return the area of the box."""
        return self.width * self.depth

    @property
    def volume(self) -> float:
        """Return the volume of this box."""
        return self.width * self.depth * self.height


@attrs(auto_attribs=True)
class Box(Generic[T], RegisterEventMixin):
    """A box on a map.

    You can create instances of this class either singly, or by using the
    :meth:`earwax.Box.create_row` method.

    If you already have a list of boxes, you can fit them all onto one map with
    the :meth:`earwax.Box.create_fitted` method.

    Boxes can be assigned arbitrary user data::

        b: Box[Enemy] = Box(start, end, data=Enemy())
        b.enemy.do_something()

    In addition to the coordinates supplied to this class's constructor, a
    :class:`earwax.BoxBounds` instance is created as :attr:`earwax.Box.bounds`.

    This class uses the `pyglet.event
    <https://pyglet.readthedocs.io/en/latest/modules/event.html>`__ framework,
    so you can register and dispatch events in the same way you would with
    ``pyglet.window.Window``, or any other ``EventDispatcher`` subclass.

    :ivar ~earwax.Box.game: The game that this box will work with.

    :ivar ~earwax.Box.start: The coordinates at the bottom rear left corner of
        this box.

    :ivar ~earwax.Box.end: The coordinates at the top front right corner of
        this box.

    :ivar ~earwax.Box.name: An optional name for this box.

    :ivar ~earwax.Box.surface_sound: The sound that should be heard when
        walking in this box.

    :ivar ~earwax.Box.wall_sound: The sound that should be heard when colliding
        with walls in this box.

    :ivar ~earwax.Box.type: The type of this box.

    :ivar ~earwax.Box.data: Arbitrary data for this box.

    :ivar ~earwax.Box.bounds: The bounds of this box.

    :ivar ~earwax.Box.centre: The point that lies at the centre of this box.

    :ivar ~earwax.Box.reverb: The reverb that is assigned to this box.
    """

    game: 'Game'
    start: Point
    end: Point

    name: Optional[str] = None
    surface_sound: Optional[Path] = None
    wall_sound: Optional[Path] = None

    type: BoxTypes = Factory(lambda: BoxTypes.empty)
    data: Optional[T] = None
    stationary: bool = Factory(lambda: True)
    bounds: BoxBounds = attrib(repr=False, init=False)
    centre: Point = attrib(init=False, repr=False)

    reverb: Optional[GlobalFdnReverb] = attrib(
        default=Factory(lambda: None), repr=False
    )
    box_level: Optional['BoxLevel'] = None
    _sound_manager: Optional[SoundManager] = attrib(
        default=Factory(lambda: None), init=False, repr=False
    )

    def __attrs_post_init__(self) -> None:
        """Configure bounds, parents and children."""
        self.bounds = BoxBounds(self.start, self.end)
        self.centre = self.start + Point(
            self.bounds.width / 2,
            self.bounds.depth / 2,
            self.bounds.height / 2
        )
        if self.box_level is not None:
            self.box_level.add_box(self)
        for func in (
            self.on_footstep, self.on_collide, self.on_activate, self.on_open,
            self.on_close
        ):
            self.register_event(cast(EventType, func))

    @classmethod
    def create_fitted(
        cls, game: 'Game', children: List['Box'],
        pad_start: Optional[Point] = None,
        pad_end: Optional[Point] = None,
        **kwargs
    ) -> 'Box':
        """Return a box that fits all of ``children`` inside itself.

        Pass a list of :class:`~earwax.Box` instances, and you'll get a box
        with its :attr:`~earwax.Box.start`, and :attr:`~earwax.Box.end`
        attributes set to match the outer bounds of the provided children.

        You can use ``pad_start``, and ``pad_end`` to add or subtract from the
        calculated start and end coordinates.

        :param children: The list of :class:`~earwax.Box` instances to
            encapsulate.

        :param pad_start: A point to add to the calculated start coordinates.

        :param pad_end: A point to add to the calculated end coordinates.

        :param kwargs: The extra keyword arguments to pass to ``Box.__init__``.
        """
        start_x: Optional[float] = None
        start_y: Optional[float] = None
        start_z: Optional[float] = None
        end_x: Optional[float] = None
        end_y: Optional[float] = None
        end_z: Optional[float] = None
        child: Box
        for child in children:
            if start_x is None or child.start.x < start_x:
                start_x = child.start.x
            if start_y is None or child.start.y < start_y:
                start_y = child.start.y
            if start_z is None or child.start.z < start_z:
                start_z = child.start.z
            if end_x is None or child.end.x > end_x:
                end_x = child.end.x
            if end_y is None or child.end.y > end_y:
                end_y = child.end.y
            if end_z is None or child.end.z > end_z:
                end_z = child.end.z
        if (
            start_x is not None and start_y is not None and
            start_z is not None and end_x is not None and
            end_y is not None and end_z is not None
        ):
            start: Point = Point(start_x, start_y, start_z)
            if pad_start is not None:
                start += pad_start
            end: Point = Point(end_x, end_y, end_z)
            if pad_end is not None:
                end += pad_end
            return cls(game, start, end, **kwargs)
        else:
            raise ValueError('Invalid children: %r.' % children)

    @classmethod
    def create_row(
        cls, game: 'Game', start: Point, size: Point, count: int,
        offset: Point, get_name: Optional[Callable[[int], str]] = None,
        on_create: Optional[Callable[['Box'], None]] = None,
        **kwargs
    ) -> List['Box']:
        """Generate a list of boxes.

        This method is useful for creating rows of buildings, or rooms on a
        corridor to name a couple of examples.

        It can be used like so::

            offices = Box.create_row(
                game,  # Every Box instance needs a game.
                Point(0, 0),  # The bottom_left corner of the first box.
                Point(3, 2, 0),  # The size of each box.
                3,  # The number of boxes to build.
                # The next argument is how far to move from the top right
                # corner of each created box:
                Point(1, 0, 0),
                # We want to name each room. For that, there is a function!
                get_name=lambda i: f'Room {i + 1}',
                # Let's make them all rooms.
                type=RoomTypes.room
            )

        This will result in a list containing 3 rooms:

        * The first from (0, 0, 0) to (2, 1, 0)

        * The second from (3, 0, 0) to (5, 1, 0)

        * And the third from (6, 0, 0) to (8, 1, 0)

        **PLEASE NOTE:**
        If none of the size coordinates are ``>= 1``, the top right coordinate
        will be less than the bottom left, so
        :meth:`~earwax.Box.get_containing_box` won't ever find it.

        :param start: The :attr:`~earwax.Box.start` coordinate of the first
            box.

        :param size: The size of each box.

        :param count: The number of boxes to build.

        :param offset: The distance between the boxes.

            If no coordinate of the given value is ``>= 1``, overlaps will
            occur.

        :param get_name: A function which should return an appropriate name.

            This function will be called with the current position in the loop.

            0 for the first room, 1 for the second, and so on.

        :param on_create: A function which will be called after each box is
            created.

            The only provided argument will be the box that was just created.

        :param kwargs: Extra keyword arguments to be passed to
            ``Box.__init__``.
        """
        start = start.copy()
        # In the next line, we subtract 1 from all size values, otherwise we
        # end up with a box that is too large by 1 on each axis.
        size -= 1
        boxes: List[Box] = []
        n: int = 0
        while n < count:
            kw: Dict[str, Any] = kwargs.copy()
            if get_name is not None:
                kw['name'] = get_name(n)
            box: Box = cls(game, start.copy(), start + size, **kw)
            if on_create is not None:
                on_create(box)
            boxes.append(box)
            if offset.x:
                start.x += offset.x + size.x
            if offset.y:
                start.y += offset.y + size.y
            if offset.z:
                start.z += offset.z + size.z
            n += 1
        return boxes

    @property
    def is_door(self) -> bool:
        """Return ``True`` if this box is a door."""
        return isinstance(self.data, Door)

    @property
    def is_portal(self) -> bool:
        """Return ``True`` if this box is a portal."""
        return isinstance(self.data, Portal)

    @property
    def sound_manager(self) -> Optional[SoundManager]:
        """Return a suitable sound manager."""
        if self._sound_manager is None:
            if self.game.audio_context is not None:
                self._sound_manager = SoundManager(
                    self.game.audio_context,
                    buffer_cache=self.game.buffer_cache,
                    default_position=self.centre,
                    default_gain=self.game.config.sound.sound_volume.value,
                    default_reverb=self.reverb
                )
                if self.name is not None:
                    self._sound_manager.name = self.name
        return self._sound_manager

    def on_footstep(self, bearing: float, coordinates: Point) -> None:
        """Play an appropriate surface sound.

        This function will be called by the Pyglet event framework, and should
        be called when a player is walking on this box.

        This event is dispatched by :class:`earwax.BoxLevel.move` upon a
        successful move.

        :param coordinates: The coordinates the player has just moved to.
        """
        pass

    def on_collide(self, coordinates: Point) -> None:
        """Play an appropriate wall sound.

        This function will be called by the Pyglet event framework, and should
        be called when a player collides with this box.
        """
        pass

    def on_activate(self) -> None:
        """Handle the enter key.

        This event is dispatched when the player presses the enter key.

        It is guaranteed that the instance this event is dispatched on is the
        one the player is stood on.
        """
        pass

    def on_open(self) -> None:
        """Handle this box being opened."""
        pass

    def on_close(self) -> None:
        """Handle this box being closed."""
        pass

    def contains_point(self, coordinates: Point) -> bool:
        """Return whether or not this box contains the given point.

        Returns ``True`` if this box spans the given coordinates, ``False``
        otherwise.

        :param coordinates: The coordinates to check.
        """
        return all(
            (
                coordinates.x >= self.start.x,
                coordinates.y >= self.start.y,
                coordinates.z >= self.start.z,
                coordinates.x <= self.end.x,
                coordinates.y <= self.end.y,
                coordinates.z <= self.end.z
            )
        )

    def could_fit(self, box: 'Box') -> bool:
        """Return whether or not the given box could be contained by this one.

        Returns ``True`` if the given box could be contained by this box,
        ``False`` otherwise.

        This method behaves like the :meth:`~earwax.Box.contains_point` method,
        except that it works with :class:`~earwax.Box` instances, rather than
        :class:`~earwax.Point` instances.

        This method doesn't care about the :attr:`~earwax.Box.parent` attribute
        on the given box. This method simply checks that the
        :attr:`~earwax.Box.start` and :attr:`~earwax.Box.end` points would fit
        inside this box.

        :param box: The box whose bounds will be checked.
        """
        return self.contains_point(box.start) and self.contains_point(box.end)

    def is_wall(self, p: Point) -> bool:
        """Return ``True`` if the provided point is inside a wall.

        :param p: The point to interrogate.
        """
        return self.type is BoxTypes.solid or (
            self.type is BoxTypes.room and self.bounds.is_edge(p)
        )

    def open(self) -> None:
        """Open the attached door.

        If this box is a door, set the :attr:`~earwax.Door.open` attribute of
        its :attr:`~earwax.Box.data` to ``True``, and play the appropriate
        sound. Otherwise, raise :class:`earwax.NotADoor`.

        :param box: The box to open.
        """
        if not isinstance(self.data, Door):
            raise NotADoor(self)
        d: Door = self.data
        if d.can_open is None or d.can_open() is True:
            d.open = True
            self.dispatch_event('on_open')
            if d.open_sound is not None:
                if self.sound_manager is None:
                    self.make_sound_manager()
                assert self.sound_manager is not None
                self.sound_manager.play_path(d.open_sound, True)
            when: float
            if isinstance(d.close_after, tuple):
                a: float
                b: float
                a, b = d.close_after
                when = uniform(a, b)
            elif isinstance(d.close_after, float):
                when = d.close_after
            else:
                return None
            schedule_once(self.scheduled_close, when)

    def close(self) -> None:
        """Close the attached door.

        If this box is a door, set the :attr:`~earwax.Door.open` attribute of
        its :attr:`~earwax.Box.data` to ``False``, and play the appropriate
        sound. Otherwise, raise :class:`earwax.NotADoor`.

        :param door: The door to close.
        """
        if not isinstance(self.data, Door):
            raise NotADoor(self)
        d: Door = self.data
        if d.can_close is None or d.can_close() is True:
            unschedule(self.scheduled_close)
            d.open = False
            self.dispatch_event('on_close')
            if d.close_sound is not None:
                if self.sound_manager is None:
                    self.make_sound_manager()
                assert self.sound_manager is not None
                self.sound_manager.play_path(d.close_sound, True)

    def scheduled_close(self, dt: float) -> None:
        """Call :meth:`~earwax.Box.close`.

        This method will be called by ``pyglet.clock.schedule_once``.

        :param dt: The ``dt`` parameter expected by Pyglet's schedule
            functions.
        """
        self.close()

    def handle_portal(self) -> None:
        """Activate a portal attached to this box."""
        assert isinstance(self.data, Portal)
        assert self.box_level is not None
        p: Portal = self.data
        if p.can_use is None or p.can_use() is True:
            if p.level is not self.box_level:
                self.game.replace_level(p.level)
            p.level.set_coordinates(p.coordinates)
            b: Optional[Box] = p.level.get_current_box()
            reverb: Optional[GlobalFdnReverb] = None
            if b is not None:
                reverb = b.reverb
            if (
                self.game.interface_sound_manager is not None
                and p.exit_sound is not None
            ):
                self.game.interface_sound_manager.play_path(
                    p.exit_sound, True, reverb=reverb
                )
            bearing: int = self.box_level.bearing
            if p.bearing is not None:
                bearing = p.bearing
            p.level.set_bearing(bearing)

    def handle_door(self) -> None:
        """Open or close the door attached to this box."""
        assert isinstance(self.data, Door)
        assert self.box_level is not None
        d: Door = self.data
        if d.open:
            self.close()
        else:
            self.open()

    def get_nearest_point(self, point: Point) -> Point:
        """Return the point on this box nearest to the provided point.

        :param point: The point to start from.
        """
        x: float
        y: float
        z: float
        if point.x < self.start.x:
            x = self.start.x
        elif point.x > self.end.x:
            x = self.end.x
        else:
            x = point.x
        if point.y < self.start.y:
            y = self.start.y
        elif point.y > self.end.y:
            y = self.end.y
        else:
            y = point.y
        if point.z < self.start.z:
            z = self.start.z
        elif point.z > self.end.z:
            z = self.end.z
        else:
            z = point.z
        return Point(x, y, z)
