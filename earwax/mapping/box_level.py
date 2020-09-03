"""Provides the BoxLevel class."""

from math import cos, dist, sin
from typing import TYPE_CHECKING, Callable, List, Optional

from attr import Factory, attrs
from movement_2d import angle2rad, coordinates_in_direction, normalise_angle
from synthizer import Context

from ..level import GameMixin, Level
from ..sound import play_and_destroy
from ..speech import tts
from ..walking_directions import walking_directions
from .box import Box
from .point import Point, PointDirections

if TYPE_CHECKING:
    from .ambiance import Ambiance


@attrs(auto_attribs=True)
class BoxLevel(Level, GameMixin):
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

    :ivar ~earwax.BoxLevel.x: The x coordinate of the perspective.

    :ivar ~earwax.BoxLevel.y: The y coordinate of the perspective.

    :ivar ~earwax.BoxLevel.bearing: The direction the perspective is facing.

    :ivar ~earwax.BoxLevel.current_box: The most recently walked over box.

        If you don't set this attribute when creating the instance, then the
        first time the player moves using the :meth:`~earwax.BoxLevel.move`
        method, the name of the box they are standing on will be spoken.
    """

    box: Box

    x: float = 0.0
    y: float = 0.0
    bearing: int = 0
    current_box: Optional[Box] = None

    ambiances: List['Ambiance'] = Factory(list)

    def start_ambiances(self) -> None:
        """Start all the ambiances on this instance."""
        ambiance: Ambiance
        for ambiance in self.ambiances:
            ambiance.start()

    def stop_ambiances(self) -> None:
        """Stops all the ambiances on this instance."""
        ambiance: Ambiance
        for ambiance in self.ambiances:
            ambiance.stop()

    def on_push(self) -> None:
        """Set listener orientation."""
        self.set_coordinates(self.x, self.y)

    def set_coordinates(self, x: float, y: float) -> None:
        """Set the current coordinates.
        Also set listener position.

        :param x: The x coordinate.

        :param y: The y coordinate.
        """
        self.x = x
        self.y = y
        if self.game.audio_context is not None:
            self.game.audio_context.position = (x, y, 0.0)

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

    def register_ambiance(self, ambiance: 'Ambiance') -> None:
        """Registers an ambiance to be handled by this level.

        :param ambiance: The ambiance to register.
        """
        self.ambiances.append(ambiance)
        ambiance.start()

    def collide(self, box: Box) -> None:
        """Called to run collision code on a box."""
        box.dispatch_event('on_collide')

    def move(self, distance: float = 1.0) -> Callable[[], None]:
        """Move on the map."""

        def inner() -> None:
            """Perform the move."""
            x: float
            y: float
            x, y = coordinates_in_direction(
                self.x, self.y, self.bearing, distance=distance
            )
            box: Optional[Box] = self.box.get_containing_box(
                Point(x, y).floor()
            )
            if box is not None:
                ctx: Optional[Context] = self.game.audio_context
                if box.wall:
                    self.collide(box)
                    box.play_sound(ctx, box.wall_sound)
                elif box.door is not None and not box.door.open:
                    self.collide(box)
                    box.play_sound(ctx, box.door.closed_sound)
                else:
                    self.set_coordinates(x, y)
                    if ctx is not None:
                        ctx.position = (x, y, 0)
                    box.dispatch_event('on_footstep')
                    if box.surface_sound is not None and ctx is not None:
                        play_and_destroy(ctx, box.surface_sound)
                    if box is not self.current_box:
                        tts.speak(str(box.name))
                        self.current_box = box

        return inner

    def show_coordinates(self) -> None:
        """Speak the current coordinates."""
        tts.speak('%d, %d' % (self.x, self.y))

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
            tts.speak(string)

        return inner

    def turn(self, amount: int) -> Callable[[], None]:
        """Return a function that will turn the perspective by the given amount.

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

        return inner

    def activate(self, door_distance: float = 2.0) -> Callable[[], None]:
        """Returns a function that you can call when the enter key is pressed.

        First we check all doors, to see if there are any close enough to open
        or close. If there are none, then dispatch the ``on_activate`` event to
        let boxes do their own thing.

        :param door_distance: How close doors have to be for this method to
            open or close them.
        """

        def inner() -> None:
            box: Optional[Box]
            for box in self.box.children:
                if box.door is not None and dist(
                    (self.x, self.y), (box.bottom_left.x, box.bottom_left.y)
                ) <= door_distance:
                    if box.door.open:
                        box.close(self.game.audio_context)
                    else:
                        box.open(self.game.audio_context)
                    break
            else:
                box = self.box.get_containing_box(Point(self.x, self.y))
                if box is not None:
                    box.dispatch_event('on_activate')

        return inner
