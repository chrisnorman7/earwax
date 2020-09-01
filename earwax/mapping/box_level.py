"""Provides the BoxLevel class."""

from math import cos, sin
from typing import Callable, List, Optional

from attr import attrs
from movement_2d import angle2rad, coordinates_in_direction, normalise_angle
from synthizer import BufferGenerator, Source
from ..walking_directions import walking_directions
from ..level import GameMixin, Level
from ..sound import play_path, schedule_generator_destruction
from ..speech import tts
from .box import Box
from .point import Point, PointDirections


@attrs(auto_attribs=True)
class BoxLevel(Level, GameMixin):
    """A level that deals with sound generation for boxes.

    This level can be used in your games. Simply bind the various action
    methods (listed below) to whatever triggers suit your purposes.

    :ivar ~earwax.BoxLevel.box: The box that this level will work with.
    """

    box: Box

    x: float = 0
    y: float = 0
    bearing: int = 0
    current_box: Optional[Box] = None

    def move(self, distance: float = 1.0) -> Callable[[], None]:
        """Move on the map."""

        def inner() -> None:
            x: float
            y: float
            x, y = coordinates_in_direction(
                self.x, self.y, self.bearing, distance=distance
            )
            box: Optional[Box] = self.box.get_containing_box(
                Point(int(x), int(y))
            )
            if box is not None:
                generator: BufferGenerator
                source: Source
                if box.wall:
                    box.dispatch_event('on_collide')
                    if box.wall_sound is not None and \
                       self.game.audio_context is not None:
                        generator, source = play_path(
                            self.game.audio_context, box.wall_sound,
                            position=(x, y, 0.0)
                        )
                        schedule_generator_destruction(generator)
                    return None
                self.set_coordinates(x, y)
                if self.game.audio_context is not None:
                    self.game.audio_context.position = (x, y, 0)
                box.dispatch_event('on_footstep')
                if box.surface_sound is not None and \
                   self.game.audio_context is not None:
                    generator, source = play_path(
                        self.game.audio_context, box.surface_sound
                    )
                    schedule_generator_destruction(generator)
                if box is not self.current_box:
                    tts.speak(str(box.name))
                    self.current_box = box

        return inner

    def on_push(self) -> None:
        """Set listener orientation."""
        self.set_coordinates(self.x, self.y)

    def show_coordinates(self) -> None:
        """Speak the current coordinates."""
        tts.speak('%d, %d' % (self.x, self.y))

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
