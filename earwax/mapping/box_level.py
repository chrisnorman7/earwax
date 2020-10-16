"""Provides the BoxLevel class."""

from math import cos, dist, sin
from typing import TYPE_CHECKING, Callable, List, Optional, Tuple

from attr import Factory, attrs
from movement_2d import angle2rad, coordinates_in_direction, normalise_angle

try:
    from pyglet.event import EventDispatcher
except ModuleNotFoundError:
    EventDispatcher = object

if TYPE_CHECKING:
    from synthizer import Context

from ..level import Level
from ..point import Point, PointDirections
from ..sound import play_and_destroy
from ..walking_directions import walking_directions
from .box import Box
from .portal import Portal


@attrs(auto_attribs=True)
class BoxLevel(Level, EventDispatcher):
    """A level that deals with sound generation for boxes.

    This level can be used in your games. Simply bind the various action
    methods (listed below) to whatever triggers suit your purposes.

    Some of the attributes of this class refer to a "perspective". This could
    theoretically be anything you want, but most likely refers to the player.
    Possible exceptions include if you made an instance to represent some kind
    of long range vision for the player.

    *Action-ready Methods*

    * :meth:`~earwax.BoxLevel.move`.

    * :meth:`~earwax.BoxLevel.show_coordinates`

    * :meth:`~earwax.BoxLevel.show_facing`

    * :meth:`~earwax.BoxLevel.turn`

    :ivar ~earwax.BoxLevel.box: The box that this level will work with.

    :ivar ~earwax.BoxLevel.coordinates: The coordinates of the perspective.

    :ivar ~earwax.BoxLevel.bearing: The direction the perspective is facing.

    :ivar ~earwax.BoxLevel.current_box: The most recently walked over box.

        If you don't set this attribute when creating the instance, then the
        first time the player moves using the :meth:`~earwax.BoxLevel.move`
        method, the name of the box they are standing on will be spoken.
    """

    box: Box

    coordinates: Point = Factory(lambda: Point(0.0, 0.0, 0.0))
    bearing: int = 0
    current_box: Optional[Box] = None

    def __attrs_post_init__(self) -> None:
        self.register_event_type('on_move')
        self.register_event_type('on_move_fail')
        self.register_event_type('on_turn')

    def on_push(self) -> None:
        """Set listener orientation, and start ambiances and tracks."""
        self.set_coordinates(self.coordinates)
        return super().on_push()

    def on_turn(self) -> None:
        """An event that will dispatched when the :meth:`~earwax.BoxLevel.turn`
        action is used.
        """
        pass

    def on_move(self) -> None:
        """An event that will be dispatched when the
        :meth:`~earwax.BoxLevel.move` action is used.
        """
        pass

    def on_move_fail(
        self, distance: float, vertical: Optional[float],
        bearing: Optional[int]
    ) -> None:
        """An event that will be dispatched when the
        :meth:`~earwax.BoxLevel.move` action has been used, but no move was
        performed.

        :param distance: The ``distance`` value that was passed to ``move()``.

        :param vertical: The ``vertical`` value that was passed to ``move``.

        :param bearing: The ``bearing`` argument that was passed to ``move``.
        """
        pass

    def set_coordinates(self, p: Point) -> None:
        """Set the current coordinates.
        Also set listener position.

        :param p: The new point to assign to :attr:`self.coordinates
            <earwax.BoxLevel.coordinates>`.
        """
        self.coordinates = p
        if self.game.audio_context is not None:
            self.game.audio_context.position = p.coordinates

    def set_bearing(self, angle: int) -> None:
        """Sets the direction of travel, and the listener orientation.

        :param angle: The bearing (in degrees).
        """
        self.bearing = angle
        if self.game.audio_context is not None:
            rad = angle2rad(angle)
            self.game.audio_context.orientation = (
                sin(rad), cos(rad), 0, 0, 0, 1
            )

    def calculate_coordinates(
        self, distance: float, bearing: int
    ) -> Tuple[float, float]:
        """Used by :meth:`~earwax.BoxLevel.move` to calculate new coordinates.

        Override this method if you want to change the algorithm used to
        calculate the target coordinates.

        :param distanc: The distance which should be used.

        :param bearing: The bearing the new coordinates are in.

            This value may not be the same as :attr:`self.bearing
            <earwax.BoxLevel.bearing>`.
        """
        return coordinates_in_direction(
            self.coordinates.x, self.coordinates.y, bearing, distance=distance
        )

    def handle_portal(self, box: Box) -> None:
        """The player has just activated a portal.

        :param box: The box that is the portal to handle.
        """
        if box.portal is not None:  # We know it is, but this keeps MyPy happy.
            p: Portal = box.portal
            if p.level is not self:
                self.game.replace_level(p.level)
            p.level.set_coordinates(p.coordinates)
            bearing: int = self.bearing
            if p.bearing is not None:
                bearing = p.bearing
            p.level.set_bearing(bearing)

    def handle_door(self, box: Box) -> None:
        """The player has just activated a door.

        :param box: The box that is the door to handle.
        """
        if box.door is not None:  # We know it is, but this keeps MyPy happy.
            if box.door.open:
                box.close(self.game.audio_context)
            else:
                box.open(self.game.audio_context)

    def handle_box(self, box: Box) -> None:
        """Handle a bulk standard box.

        The coordinates have already been set, and the ``on_footstep`` event
        dispatched, so all that is left is to speak the name of the new box, if
        it is different to the last one, and play the ``surface_sound`` sound.
        """
        ctx: Optional['Context'] = self.game.audio_context
        if box.surface_sound is not None and ctx is not None:
            play_and_destroy(ctx, box.surface_sound)
        if box is not self.current_box:
            if (
                self.current_box is not None and
                box.name != self.current_box.name
            ):
                self.game.output(str(box.name))
            self.current_box = box

    def collide(self, box: Box) -> None:
        """Called to run collision code on a box."""
        box.dispatch_event('on_collide')

    def move(
        self, distance: float = 1.0, vertical: Optional[float] = None,
        bearing: Optional[int] = None
    ) -> Callable[[], None]:
        """Returns a callable that allows the player to move on the map.

        If the move is successfl (I.E.: There is a box at the destination
        coordinates), the :meth:`~earwax.BoxLevel.on_move` event is dispatched.

        If not, then :meth:`~earwax.BoxLevel.on_move_fail` is dispatched.

        :param distance: The distance to move.

        :param vertical: An optional adjustment to be added to the vertical
            position.

        :param bearing: An optional direction to move in.

            If this value is ``None``, then :attr:`self.bearing
            <earwax.BoxLevel.bearing>` will be used.
        """

        def inner() -> None:
            """Perform the move."""
            x: float
            y: float
            z: float = self.coordinates.z
            if vertical is not None:
                z += vertical
            _bearing: int = self.bearing if bearing is None else bearing
            x, y = self.calculate_coordinates(distance, _bearing)
            p: Point = Point(x, y, z)
            box: Optional[Box] = self.box.get_containing_box(p.floor())
            if box is not None:
                ctx: Optional['Context'] = self.game.audio_context
                if box.wall:
                    self.collide(box)
                    box.play_sound(ctx, box.wall_sound)
                elif box.door is not None and not box.door.open:
                    self.collide(box)
                    box.play_sound(ctx, box.door.closed_sound)
                else:
                    self.set_coordinates(p)
                    box.dispatch_event('on_footstep')
                    self.handle_box(box)
                self.dispatch_event('on_move')
            else:
                self.dispatch_event(
                    'on_move_fail', distance, vertical, bearing
                )

        return inner

    def show_coordinates(self, include_z: bool = False) -> Callable[[], None]:
        """Speak the current coordinates."""

        def inner() -> None:
            """Speak the coordinates."""
            c: Point = self.coordinates.floor()
            s: str = f'{c.x}, {c.y}'
            if include_z:
                s += f', {c.z}'
            self.game.output(s)

        return inner

    def show_facing(self, include_angle: bool = True) -> Callable[[], None]:
        """Returns a function that will let you see the current bearing as text::

            l = BoxLevel(...)
            l.action('Show facing', symbol=key.F)(l.show_facing())

        :param include_angle: If ``True``, then the actual angle will be shown
            along with the direction name.
        """

        def inner() -> None:
            directions: List[PointDirections] = list(walking_directions)
            directions.remove(PointDirections.here)
            index: int = round(
                (
                    self.bearing + 360 if (self.bearing % 360) < 0 else
                    self.bearing
                ) / 45
            ) % len(directions)
            string: str = directions[index].name
            if include_angle:
                string = f'{string} ({self.bearing})'
            self.game.output(string)

        return inner

    def turn(self, amount: int) -> Callable[[], None]:
        """Return a function that will turn the perspective by the given amount,
        and dispatch the ``on_turn`` event.

        For example::

            l = BoxLevel(...)
            l.action('Turn right', symbol=key.D)(l.turn(45))
            l.action('Turn left', symbol=key.A)(l.turn(-45))

        The resulting angle will always be in the range 0-359.

        :param amount: The amount to turn by.

            Positive numbers turn clockwise, while negative numbers turn
            anticlockwise.
        """

        def inner() -> None:
            self.set_bearing(normalise_angle(self.bearing + amount))
            self.dispatch_event('on_turn')

        return inner

    def activate(self, door_distance: float = 2.0) -> Callable[[], None]:
        """Returns a function that you can call when the enter key is pressed.

        First we check if the current box is a portal. If it is, then we call
        :meth:`~earwax.BoxLevel.handle_portal`.

        Second we check all doors, to see if there are any close enough to open
        or close. If there are, then we call
        :meth:`~earwax.BoxLevel.handle_door`. Otherwise, dispatch the
        ``on_activate`` event to let boxes do their own thing.

        :param door_distance: How close doors have to be for this method to
            open or close them.
        """

        def inner() -> None:
            box: Optional[Box] = self.box.get_containing_box(self.coordinates)
            if box is not None and box.portal is not None:
                return self.handle_portal(box)
            child: Box
            for child in self.box.children:
                if child.door is not None and dist(
                    self.coordinates.coordinates, child.bottom_left.coordinates
                ) <= door_distance:
                    return self.handle_door(child)
            if box is not None:
                box.dispatch_event('on_activate')

        return inner
