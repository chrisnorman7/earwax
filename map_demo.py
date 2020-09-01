from typing import Callable, Generator, List, Optional

from math import pi, cos, sin
from pyglet.window import Window, key
from synthizer import BufferGenerator, Source, Source3D

from earwax import (Box, Editor, FittedBox, Game, Level, Point,
                    PointDirections, box_row, play_path,
                    schedule_generator_destruction, tts, walking_directions)
from earwax.cmd.constants import sounds_directory, surfaces_directory

wall_sounds = sounds_directory / 'walls'

boxes: List[Box] = [
    Box(
        Point(0, 0), Point(100, 2), name='Main Corridor',
        surface_sound=surfaces_directory / 'gridwork'
    ),
    Box(Point(0, 3), Point(0, 12), wall=True, wall_sound=wall_sounds),
]

index: int
box: Box
for index, box in enumerate(box_row(Point(1, 4), 19, 9, 5, 2, 0)):
    box.surface_sound = surfaces_directory / 'concrete'
    box.name = f'Office {index + 1}'
    boxes.append(box)

boxes.extend(
    box_row(Point(20, 4), 1, 9, 5, 20, 0, wall=True, wall_sound=wall_sounds)
)

boxes.extend(
    box_row(Point(1, 3), 100, 1, 2, 0, 10, wall=True, wall_sound=wall_sounds)
)

main_box: FittedBox = FittedBox(boxes, name='Error')


class MapDemoGame(Game):
    def before_run(self) -> None:
        super().before_run()
        if self.audio_context is not None:
            rad: float = (0 / 180.0) * pi
            self.audio_context.orientation = (sin(rad), cos(rad), 0, 0, 0, 1)


game: MapDemoGame = MapDemoGame()
window: Window = Window(caption='Map Demo')
coordinates: Point = Point(0, 0)
old_box: Box = boxes[0]
level = Level()


@level.action('Show coordinates', symbol=key.K)
def show_coordinates() -> None:
    """Speak the current coordinates."""
    tts.speak(f'{coordinates.x}, {coordinates.y}')


@level.action('Quit', symbol=key.ESCAPE)
def do_quit() -> None:
    """Quit the game."""
    window.dispatch_event('on_close')


@level.action('Goto', symbol=key.G)
def goto() -> Generator[None, None, None]:
    """Jump to some coordinates."""
    dest: Point = coordinates.copy()

    def y_inner(value: str) -> None:
        """Set the y coordinate, and jump the player."""
        try:
            dest.y = int(value)
            if dest == coordinates:
                tts.speak('Coordinates unchanged.')
                return None
            coordinates.x = dest.x
            coordinates.y = dest.y
            tts.speak('Moved.')
        except ValueError:
            tts.speak('Invalid coordinate.')
        finally:
            game.pop_level()

    def x_inner(value: str) -> Generator[None, None, None]:
        """Set the x coordinate."""
        try:
            dest.x = int(value)
            yield
            game.replace_level(Editor(y_inner, game, text=str(coordinates.y)))
            tts.speak(f'Y coordinate: {coordinates.y}')
        except ValueError:
            tts.speak('Invalid coordinate.')
            game.pop_level()

    yield
    game.push_level(Editor(x_inner, game, text=str(coordinates.x)))
    tts.speak(f'X coordinate: {coordinates.x}')


def move(direction: PointDirections) -> Callable[[], None]:
    """Move on the map."""

    def inner() -> None:
        global old_box
        x: int
        y: int
        x, y = walking_directions[direction]
        x += coordinates.x
        y += coordinates.y
        box: Optional[Box] = main_box.get_containing_box(Point(x, y))
        if box is not None:
            generator: BufferGenerator
            source: Source
            if box.wall:
                box.dispatch_event('on_collide')
                if box.wall_sound is not None and \
                   game.audio_context is not None:
                    source = Source3D(game.audio_context)
                    source.position = (x, y, 0)
                    print(source.position)
                    generator, source = play_path(
                        game.audio_context, box.wall_sound, source=source
                    )
                    schedule_generator_destruction(generator)
                return None
            coordinates.x = x
            coordinates.y = y
            if game.audio_context is not None:
                game.audio_context.position = (x, y, 0)
            box.dispatch_event('on_footstep')
            if box.surface_sound is not None and \
               game.audio_context is not None:
                generator, source = play_path(
                    game.audio_context, box.surface_sound
                )
                schedule_generator_destruction(generator)
            if box is not old_box:
                tts.speak(str(box.name))
                old_box = box

    return inner


def main() -> None:
    name: str
    symbol: int
    direction: PointDirections
    for name, symbol, direction in [
        ('North', key.I, PointDirections.north),
        ('Northeast', key.O, PointDirections.northeast),
        ('East', key.L, PointDirections.east),
        ('Southeast', key.PERIOD, PointDirections.southeast),
        ('South', key.COMMA, PointDirections.south),
        ('Southwest', key.M, PointDirections.southwest),
        ('West', key.J, PointDirections.west),
        ('Northwest', key.U, PointDirections.northwest)
    ]:
        level.action(name, symbol=symbol)(move(direction))
    game.push_level(level)
    game.run(window)


if __name__ == '__main__':
    main()
