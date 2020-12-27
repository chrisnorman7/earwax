"""Provides the BoxLevel class."""

from math import cos, floor, sin
from typing import Callable, List, Optional, Tuple, cast

from attr import Factory, attrib, attrs
from movement_2d import angle2rad, coordinates_in_direction, normalise_angle

from ..types import EventType
from .box import BoxBounds

try:
    from synthizer import Context, GlobalFdnReverb, Source3D
except ModuleNotFoundError:
    Context, Source3D, GlobalFdnReverb = (None, None, None)

from ..level import Level
from ..point import Point, PointDirections
from ..sound import SoundManager
from ..walking_directions import walking_directions
from .box import Box, ReverbSettingsDict
from .portal import Portal


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

    :ivar ~earwax.BoxLevel.player_sound_manager: The sound manager to use to
        play sounds that are generated by the player (footsteps for example).


    :ivar ~earwax.BoxLevel.reverb: An optional reverb to play sounds through.

        You shouldn't write to this property, instead use the
        :meth:`~earwax.BoxLevel.connect_reverb` method to set a new reverb, and
        :meth:`~earwax.BoxLevel.disconnect_reverb` to clear.
    """

    box: Box

    coordinates: Point = attrib()

    @coordinates.default
    def get_default_coordinates(instance: 'BoxLevel') -> Point:
        """Return the start coordinates for the contained box.

        :param instance: The instance whose ``box`` attribute's start
            coordinates will be returned.
        """
        return instance.box.start

    bearing: int = 0
    current_box: Optional[Box] = None

    player_sound_manager: Optional[SoundManager] = None
    reverb: Optional[GlobalFdnReverb] = attrib(
        default=Factory(type(None)), repr=False, init=False
    )

    def __attrs_post_init__(self) -> None:
        """Register default events."""
        super().__attrs_post_init__()
        for func in (self.on_move, self.on_move_fail, self.on_turn):
            self.register_event(cast(EventType, func))

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

    def on_move(self) -> None:
        """Handle movement.

        An event that will be dispatched when the
        :meth:`~earwax.BoxLevel.move` action is used.

        By default, this method plays the correct footstep sound.
        """
        box: Optional[Box] = self.get_current_box()
        if (
            box is not None and self.player_sound_manager is not None and
            box.surface_sound is not None
        ):
            self.player_sound_manager.play_path(box.surface_sound, True)

    def on_move_fail(
        self, distance: float, vertical: Optional[float],
        bearing: Optional[int], coordinates: Point
    ) -> None:
        """Handle a move failure.

        An event that will be dispatched when the
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
        """Set the direction of travel and the listener's orientation.

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
        """Calculate coordinates at the given distance in the given direction.

        Used by :meth:`~earwax.BoxLevel.move` to calculate new coordinates.

        Override this method if you want to change the algorithm used to
        calculate the target coordinates.

        :param distance: The distance which should be used.

        :param bearing: The bearing the new coordinates are in.

            This value may not be the same as :attr:`self.bearing
            <earwax.BoxLevel.bearing>`.
        """
        return coordinates_in_direction(
            self.coordinates.x, self.coordinates.y, bearing, distance=distance
        )

    def update_reverb(self, data: ReverbSettingsDict) -> None:
        """Update :attr:`self.reverb <earwax.BoxLevel.reverb>` from ``data``.

        :param data: The data to update reverb settings from.
        """
        if self.reverb is None:
            raise RuntimeError('No reverb has been set.')
        name: str
        value: float
        for name, value in data.items():
            setattr(self.reverb, name, value)

    def handle_portal(self, box: Box) -> None:
        """Activate a portal.

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
        """Activate a door.

        :param box: The box that is the door to handle.
        """
        if box.door is not None:  # We know it is, but this keeps MyPy happy.
            if box.door.open:
                box.close()
            else:
                box.open()

    def handle_box(self, box: Box) -> None:
        """Handle a bulk standard box.

        The coordinates have already been set, and the ``on_footstep`` event
        dispatched, so all that is left is to speak the name of the new box, if
        it is different to the last one, update :attr:`self.reverb
        <earwax.BoxLevel.reverb>` if necessary, and store the new box.
        """
        if box is not self.current_box:
            if self.reverb is not None:
                self.update_reverb(box.reverb_settings)
            if (
                self.current_box is not None and
                box.name != self.current_box.name
            ):
                self.game.output(str(box.name))
            self.current_box = box

    def collide(self, box: Box, coordinates: Point) -> None:
        """Handle collitions.

        Called to run collision code on a box.

        :param box: The box the player collided with.

        :param coordinates: The coordinates the player was trying to reach.
        """
        if self.player_sound_manager is not None:
            if box.door is not None and not box.door.open:
                # Play a closed door sound, instead of a wall sound.
                if box.door.closed_sound is not None:
                    self.player_sound_manager.play_path(
                        box.door.closed_sound, True
                    )
            elif box.wall_sound is not None:
                self.player_sound_manager.play_path(box.wall_sound, True)
        box.dispatch_event('on_collide', coordinates)

    def move(
        self, distance: float = 1.0, vertical: Optional[float] = None,
        bearing: Optional[int] = None
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
            box: Optional[Box] = self.box.get_containing_box(p.floor())
            if box is not None:
                if box.is_wall(p) or (
                    box.door is not None and not box.door.open
                ):
                    self.collide(box, p)
                else:
                    self.set_coordinates(p)
                    box.dispatch_event('on_footstep', _bearing, p)
                    self.handle_box(box)
                    self.dispatch_event('on_move')
            else:
                self.dispatch_event(
                    'on_move_fail', distance, vertical, _bearing, p
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
            self.dispatch_event('on_turn')

        return inner

    def activate(self, door_distance: float = 2.0) -> Callable[[], None]:
        """Return a function that can be call when the enter key is pressed.

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
            """Activate."""
            box: Optional[Box] = self.get_current_box()
            if box is not None and box.portal is not None:
                return self.handle_portal(box)
            child: Box
            for child in self.box.get_descendants():
                if (
                    child.door is not None and
                    self.coordinates.distance_between(
                        child.start
                    ) <= door_distance
                ):
                    return self.handle_door(child)
            if box is not None:
                box.dispatch_event('on_activate')

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
            d: Optional[Box] = self.box.nearest_door(self.coordinates)
            if d is not None:
                name: str = d.name or 'Untitled door'
                angle: int = floor(self.get_angle_between(d.start))
                distance: float = self.coordinates.distance_between(d.start)
                directions: str
                if not round(distance):
                    directions = 'here'
                else:
                    directions = '%.1f at %d degrees' % (distance, angle)
                if max_distance is None or distance < max_distance:
                    return self.game.output(f'{name}: {directions}.')
            self.game.output('There are no nearby doors.')

        return inner

    def describe_current_box(self) -> None:
        """Describe the current box."""
        box: Optional[Box] = self.get_current_box()
        if box is None:
            self.game.output('No box.')
        else:
            b: BoxBounds = box.bounds
            self.game.output(
                f'{box.name}: {b.width + 1} x {b.depth + 1} x {b.height + 1}.'
            )

    def get_current_box(self) -> Optional[Box]:
        """Get the box that lies at the current coordinates."""
        return self.box.get_containing_box(self.coordinates.floor())

    def get_angle_between(self, other: Point) -> float:
        """Return the angle between the perspective and the other coordinates.

        This function takes into account :attr:`self.bearing
        <earwax.BoxLevel.bearing>`.

        :param other: The target coordinates.
        """
        angle: float = self.coordinates.angle_between(other)
        return normalise_angle(angle - self.bearing)

    def connect_reverb(
        self, reverb: GlobalFdnReverb, override: bool = True
    ) -> None:
        """Set a new reverb.

        This method should be preferred over setting
        :attr:`~earwax.BoxLevel.reverb`, as it handles the attached sound
        managers.

        :param reverb: The reverb to connect.

        :param override: If ``True``, then any old reverb will be disconnected
            before a new one is added.
        """
        if self.reverb is not None and override:
            self.disconnect_reverb()
        self.reverb = reverb
        if self.player_sound_manager is not None:
            self.player_sound_manager.context.config_route(
                self.player_sound_manager.source, reverb
            )

    def disconnect_reverb(self) -> None:
        """Disconnect any connected :attr:`~earwax.BoxLevel.reverb`.

        This method should be preferred over setting reverb to ``None``, as it
        correctly handles connected sound managers.
        """
        if self.player_sound_manager is not None:
            self.player_sound_manager.context.remove_route(
                self.player_sound_manager.source, self.reverb
            )
        self.reverb = None
