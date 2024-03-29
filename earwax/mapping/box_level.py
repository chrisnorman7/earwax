"""Provides the BoxLevel class."""

from math import cos, floor, sin
from typing import (
    Any, Callable, Dict, Iterable, List, Optional, Tuple, Type, cast)

from attr import Factory, attrib, attrs
from movement_2d import angle2rad, coordinates_in_direction, normalise_angle

from ..hat_directions import DOWN, LEFT, RIGHT, UP
from ..types import EventType
from .box import BoxBounds, BoxTypes

try:
    from synthizer import Context, GlobalFdnReverb
except ModuleNotFoundError:
    Context, GlobalFdnReverb = (object, object)

from pyglet.window import key

from ..level import Level
from ..point import Point, PointDirections
from ..walking_directions import walking_directions
from .box import Box
from .door import Door
from .portal import Portal


@attrs(auto_attribs=True)
class CurrentBox:
    """Store a reference to the current box.

    This class stores the position too, so that caching can be performed.

    :ivar ~earwax.CurrentBox.coordinates: The coordinates that were last
        checked.

    :ivar ~earwax.CurrentBox.box: The last current box.
    """

    coordinates: Point
    box: Box[Any]


@attrs(auto_attribs=True)
class NearestBox:
    """A reference to the nearest box.

    :ivar ~earwax.NearestBox.box: The box that was found.

    :ivar ~earwax.NearestBox.coordinates: The nearest coordinates to the ones
        specified.

    :ivar ~earwax.NearestBox.distance: The distance between the supplied
        coordinates, and :attr:`~earwax.NearestBox.coordinates`.
    """

    box: Box
    coordinates: Point
    distance: float


@attrs(auto_attribs=True)
class BoxLevel(Level):
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

    * :meth:`~earwax.BoxLevel.show_nearest_door`

    * :meth:`~earwax.BoxLevel.describe_current_box`

    :ivar ~earwax.BoxLevel.box: The box that this level will work with.

    :ivar ~earwax.BoxLevel.coordinates: The coordinates of the perspective.

    :ivar ~earwax.BoxLevel.bearing: The direction the perspective is facing.

    :ivar ~earwax.BoxLevel.current_box: The most recently walked over box.

        If you don't set this attribute when creating the instance, then the
        first time the player moves using the :meth:`~earwax.BoxLevel.move`
        method, the name of the box they are standing on will be spoken.

    :ivar ~earwax.BoxLevel.reverb: An optional reverb to play sounds through.

        You shouldn't write to this property, instead use the
        :meth:`~earwax.BoxLevel.connect_reverb` method to set a new reverb, and
        :meth:`~earwax.BoxLevel.disconnect_reverb` to clear.
    """

    boxes: List[Box[Any]] = Factory(list)
    boxes_by_type: Dict[Type, List[Box]] = attrib(
        default=Factory(dict), init=False, repr=False
    )

    coordinates: Point = Factory(lambda: Point(0, 0, 0))

    bearing: int = 0
    current_box: Optional[CurrentBox] = None

    def __attrs_post_init__(self) -> None:
        """Register default events."""
        super().__attrs_post_init__()
        for func in (self.on_move_success, self.on_move_fail, self.on_turn):
            self.register_event(cast(EventType, func))
        box: Box
        for box in self.boxes:
            self.register_box(box)

    def add_default_actions(self) -> None:
        """Add some default actions.

        This method adds the following actions:

        * Move forward: W

        * Turn 180 degrees: S

        * Turn 45 degrees left: A

        * Turn 45 degrees right: D

        * Show coordinates: C

        * Show the facing direction: F

        * Describe current box: X

        * Speak nearest door: Z

        * Activate nearby objects: Return
        """
        self.action(
            "Move forwards", symbol=key.W, hat_direction=UP, interval=0.5
        )(self.move())
        self.action("Turn around", symbol=key.S, hat_direction=DOWN)(
            self.turn(180)
        )
        self.action("Turn left", symbol=key.A, hat_direction=LEFT)(
            self.turn(-45)
        )
        self.action("Turn right", symbol=key.D, hat_direction=RIGHT)(
            self.turn(45)
        )
        self.action("Show coordinates", symbol=key.C, joystick_button=0)(
            self.show_coordinates()
        )
        self.action("Show facing direction", symbol=key.F, joystick_button=3)(
            self.show_facing()
        )
        self.action("Describe current box", symbol=key.X, joystick_button=2)(
            self.describe_current_box
        )
        self.action("Show nearest door", symbol=key.Z, joystick_button=1)(
            self.show_nearest_door()
        )
        self.action("Activate nearby objects", symbol=key.RETURN)(
            self.activate()
        )

    def add_box(self, box: Box[Any]) -> None:
        """Add a box to :attr:`self.boxes <earwax.BoxLevel.boxes>`.

        :param box: The box to add.
        """
        self.boxes.append(box)
        self.register_box(box)

    def register_box(self, box: Box) -> None:
        """Register a box that is already in the boxes list.

        :param box: The box to register.
        """
        box.box_level = self
        data_type = type(box.data)
        if data_type not in self.boxes_by_type:
            self.boxes_by_type[data_type] = []
        self.boxes_by_type[data_type].append(box)
        if self.current_box is not None and box.contains_point(
            self.current_box.coordinates
        ):
            self.current_box = None

    def remove_box(self, box: Box[Any]) -> None:
        """Remove a box from :attr:`self.boxes <earwax.BoxLevel.boxes>`.

        :param box: The box to remove.
        """
        box.box_level = None
        self.boxes.remove(box)
        self.current_box = None
        data_type = type(box.data)
        if data_type in self.boxes_by_type:
            self.boxes_by_type[data_type].remove(box)
            if not self.boxes_by_type[data_type]:
                del self.boxes_by_type[data_type]
        if self.current_box is not None and box.contains_point(
            self.current_box.coordinates
        ):
            self.current_box = None

    def add_boxes(self, boxes: Iterable[Box]) -> None:
        """Add multiple boxes with one call.

        :param boxes: An iterable for boxes to add.
        """
        box: Box
        for box in boxes:
            self.add_box(box)

    def on_push(self) -> None:
        """Set listener orientation, and start ambiances and tracks."""
        self.set_coordinates(self.coordinates)
        return super().on_push()

    def on_turn(self) -> None:
        """Handle turning.

        An event that will dispatched when the :meth:`~earwax.BoxLevel.turn`
        action is used.
        """
        pass

    def on_move_success(self) -> None:
        """Handle a successful move.

        An event that will be dispatched when the
        :meth:`~earwax.BoxLevel.move` action is used.

        By default, this method plays the correct footstep sound.
        """
        box: Optional[Box] = self.get_current_box()
        if (
            box is not None
            and box.sound_manager is not None
            and box.surface_sound is not None
        ):
            box.sound_manager.play_path(box.surface_sound, position=None)

    def on_move_fail(
        self,
        distance: float,
        vertical: Optional[float],
        bearing: int,
        coordinates: Point,
    ) -> None:
        """Handle a move failure.

        An event that will be dispatched when the
        :meth:`~earwax.BoxLevel.move` action has been used, but no move was
        performed.

        :param distance: The ``distance`` value that was passed to ``move()``.

        :param vertical: The ``vertical`` value that was passed to ``move``.

        :param bearing: The ``bearing`` argument that was passed to ``move``,
            or :attr:`self.bearing <earwax.BoxLevel.bearing>`.
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
        """Set the direction of travel and the listener's orientation.

        :param angle: The bearing (in degrees).
        """
        self.bearing = angle
        if self.game.audio_context is not None:
            rad = angle2rad(angle)
            self.game.audio_context.orientation = (
                sin(rad),
                cos(rad),
                0,
                0,
                0,
                1,
            )

    def calculate_coordinates(
        self, distance: float, bearing: int
    ) -> Tuple[float, float]:
        """Calculate coordinates at the given distance in the given direction.

        Used by :meth:`~earwax.BoxLevel.move` to calculate new coordinates.

        Override this method if you want to change the algorithm used to
        calculate the target coordinates.

        Please bear in mind however, that the coordinates this method returns
        should always be 2d.

        :param distance: The distance which should be used.

        :param bearing: The bearing the new coordinates are in.

            This value may not be the same as :attr:`self.bearing
            <earwax.BoxLevel.bearing>`.
        """
        return coordinates_in_direction(
            self.coordinates.x, self.coordinates.y, bearing, distance=distance
        )

    def handle_box(self, box: Box[Any]) -> None:
        """Handle a bulk standard box.

        The coordinates have already been set, and the ``on_footstep`` event
        dispatched, so all that is left is to speak the name of the new box, if
        it is different to the last one, update :attr:`self.reverb
        <earwax.BoxLevel.reverb>` if necessary, and store the new box.
        """
        current_box: Optional[Box] = None
        if self.current_box is not None:
            current_box = self.current_box.box
        self.current_box = CurrentBox(self.coordinates, box)
        if box is not current_box:
            if (
                current_box is not None
                and box.name != current_box.name
                and box.name is not None
            ):
                self.game.output(box.name)

    def collide(self, box: Box[Any], coordinates: Point) -> None:
        """Handle collitions.

        Called to run collision code on a box.

        :param box: The box the player collided with.

        :param coordinates: The coordinates the player was trying to reach.
        """
        data: Any = box.data
        if box.sound_manager is not None:
            if box.is_door and not data.open:
                # Play a closed door sound, instead of a wall sound.
                if data.closed_sound is not None:
                    box.sound_manager.play_path(
                        data.closed_sound, position=coordinates
                    )
            elif box.wall_sound is not None and box.sound_manager is not None:
                box.sound_manager.play_path(
                    box.wall_sound, position=coordinates
                )
        box.dispatch_event("on_collide", coordinates)

    def move(
        self,
        distance: float = 1.0,
        vertical: Optional[float] = None,
        bearing: Optional[int] = None,
    ) -> Callable[[], None]:
        """Return a callable that allows the player to move on the map.

        If the move is successful (I.E.: There is a box at the destination
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
            box: Optional[Box[Any]] = self.get_containing_box(p.floor())
            if box is not None:
                if box.is_wall(p) or (
                    isinstance(box.data, Door) and not box.data.open
                ):
                    self.collide(box, p)
                else:
                    self.set_coordinates(p)
                    box.dispatch_event("on_footstep", _bearing, p)
                    self.handle_box(box)
                    self.dispatch_event("on_move_success")
            else:
                self.dispatch_event(
                    "on_move_fail", distance, vertical, _bearing, p
                )

        return inner

    def show_coordinates(self, include_z: bool = False) -> Callable[[], None]:
        """Speak the current coordinates."""

        def inner() -> None:
            """Speak the coordinates."""
            c: Point = self.coordinates.floor()
            s: str = f"{c.x}, {c.y}"
            if include_z:
                s += f", {c.z}"
            self.game.output(s)

        return inner

    def show_facing(self, include_angle: bool = True) -> Callable[[], None]:
        """Return a function that will let you see the current bearing as text.

        For example::

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
                    self.bearing + 360
                    if (self.bearing % 360) < 0
                    else self.bearing
                )
                / 45
            ) % len(directions)
            string: str = directions[index].name
            if include_angle:
                string = f"{string} ({self.bearing})"
            self.game.output(string)

        return inner

    def turn(self, amount: int) -> Callable[[], None]:
        """Return a turn function.

        Return a function that will turn the perspective by the given amount
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
            self.dispatch_event("on_turn")

        return inner

    def activate(self, door_distance: float = 2.0) -> Callable[[], None]:
        """Return a function that can be call when the enter key is pressed.

        First we check if the current box is a portal. If it is, then we call
        :meth:`~earwax.Box.handle_portal`.

        If it is not, we check to see if there is a door close enough to be
        opened or closed. If there is, then we call
        :meth:`~earwax.Box.handle_door` on it.

        If none of this works, and there is a current box, dispatch the
        :meth:`~earwax.Box.on_activate` event to let the box do its own thing.

        :param door_distance: How close doors have to be for this method to
            open or close them.
        """

        def inner() -> None:
            """Activate."""
            box: Optional[Box[Any]] = self.get_current_box()
            if box is not None and box.is_portal:
                return box.handle_portal()
            nearest_door: Optional[NearestBox] = self.nearest_door(
                self.coordinates
            )
            if (
                nearest_door is not None
                and nearest_door.distance <= door_distance
            ):
                return nearest_door.box.handle_door()
            if box is not None:
                box.dispatch_event("on_activate")

        return inner

    def show_nearest_door(
        self, max_distance: Optional[float] = None
    ) -> Callable[[], None]:
        """Return a callable that will speak the position of the nearest door.

        :param max_distance: The maximum distance between the current
            coordinates and the nearest door where the door will still be
            reported.

            If this value is ``None``, then any door will be reported.
        """

        def inner() -> None:
            nearest_door: Optional[NearestBox] = self.nearest_door(
                self.coordinates
            )
            if nearest_door is not None:
                d: Box[Door] = nearest_door.box
                name: str = d.name or "Untitled door"
                angle: int = floor(
                    self.get_angle_between(nearest_door.coordinates)
                )
                distance: float = nearest_door.distance
                if max_distance is not None and distance > max_distance:
                    return self.game.output("There are no nearby doors.")
                directions: str
                if not round(distance):
                    directions = "here"
                else:
                    directions = "%.1f at %d degrees" % (distance, angle)
                self.game.output(f"{name}: {directions}.")

        return inner

    def describe_current_box(self) -> None:
        """Describe the current box."""
        box: Optional[Box] = self.get_current_box()
        if box is None:
            self.game.output("No box.")
        else:
            b: BoxBounds = box.bounds
            self.game.output(
                f"{box.name}: {b.width + 1} x {b.depth + 1} x {b.height + 1}."
            )

    def get_current_box(self) -> Optional[Box]:
        """Get the box that lies at the current coordinates."""
        if (
            self.current_box is not None
            and self.current_box.coordinates == self.coordinates
        ):
            return self.current_box.box
        box: Optional[Box] = self.get_containing_box(self.coordinates)
        if box is None:
            self.current_box = None
        else:
            self.current_box = CurrentBox(self.coordinates, box)
        return box

    def get_angle_between(self, other: Point) -> float:
        """Return the angle between the perspective and the other coordinates.

        This function takes into account :attr:`self.bearing
        <earwax.BoxLevel.bearing>`.

        :param other: The target coordinates.
        """
        angle: float = self.coordinates.angle_between(other)
        return normalise_angle(angle - self.bearing)

    def nearest_by_type(
        self, start: Point, data_type: Any, same_z: bool = True
    ) -> Optional[NearestBox]:
        """Get the nearest box to the given point by type.

        If no boxes of the given type are found, ``None`` will be returned.

        :param start: The point to start looking from.

        :param data_type: The type of :attr:`box data <earwax.Box.data>` to
            search for.

        :param same_z: If this value is ``True``, only boxes on the same z axis
            will be considered.
        """
        nearest: Optional[NearestBox] = None
        box: Box
        for box in self.get_boxes(data_type):
            point: Point = box.get_nearest_point(start)
            if not same_z or box.start.z == start.z:
                distance: float = start.distance_between(point)
                if nearest is None or distance < nearest.distance:
                    nearest = NearestBox(box, point, distance)
        return nearest

    def nearest_door(
        self, start: Point, same_z: bool = True
    ) -> Optional[NearestBox]:
        """Get the nearest door.

        Iterates over all doors, and returned the nearest one.

        :param start: The coordinates to start from.

        :param same_z: If ``True``, then doors on different levels will not be
            considered.
        """
        return self.nearest_by_type(start, Door, same_z=same_z)

    def nearest_portal(
        self, start: Point, same_z: bool = True
    ) -> Optional[NearestBox]:
        """Return the nearest portal.

        :param start: The coordinates to start from.

        :param same_z: If ``True``, then portals on different levels will not
            be considered.
        """
        return self.nearest_by_type(start, Portal, same_z=same_z)

    def sort_boxes(self) -> List[Box]:
        """Return :attr:`~earwax.Box.children` sorted by area."""
        return sorted(self.boxes, key=lambda c: c.bounds.area)

    def get_containing_box(self, coordinates: Point) -> Optional[Box]:
        """Return the box that spans the given coordinates.

        If no box is found, ``None`` will be returned.

        This method scans :attr:`self.boxes <earwax.BoxLevel.boxes>` using  the
        :meth:`~earwax.BoxLevel.sort_boxes` method.

        :param coordinates: The coordinates the box should span.
        """
        box: Box
        for box in self.sort_boxes():
            if box.contains_point(coordinates):
                return box
        else:
            return None

    def get_boxes(self, t: Any) -> List[Box]:
        """Return a list of boxes of the current type.

        If no boxes are found, an empty list is returned.

        :param t: The type of the boxes.
        """
        return self.boxes_by_type.get(t, [])

    def walls_between(self, end: Point, start: Optional[Point] = None) -> int:
        """Return the number of walls between two points.

        :param end: The target coordinates.

        :param start: The coordinates to start at.

            If this value is ``None``, then the current
            :attr:`~earwax.BoxLevel.coordinates` will be used.
        """
        if start is None:
            start = self.coordinates
        start_x: int = min(start.x, end.x)
        start_y: int = min(start.y, end.y)
        start_z: int = min(start.z, end.z)
        end_x: int = max(start.x, end.x)
        end_y: int = max(start.y, end.y)
        end_z: int = max(start.z, end.z)
        b: Box
        boxes: List[Box] = [
            b
            for b in self.boxes
            if b.start.x >= start_x
            and b.start.y >= start_y
            and b.start.z >= start_z
            and b.end.x <= end_x
            and b.end.y <= end_y
            and b.end.z <= end_z
            and b.type is not BoxTypes.empty
        ]
        return len(boxes)
