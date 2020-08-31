from typing import Callable, List, Optional

from pyglet.window import Window, key

from earwax import (Box, FittedBox, Game, Level, Point, PointDirections,
                    box_row, tts, walking_directions)
from earwax.cmd.constants import surfaces_directory

boxes: List[Box] = [
    Box(
        Point(0, 0), Point(99, 2), name='Main Corridor',
        surface_sound=surfaces_directory / 'gridwork'
    )
]
index: int
box: Box
for index, box in enumerate(box_row(Point(0, 3), 20, 10, 5, 1, 0)):
    box.surface_sound = surfaces_directory / 'concrete'
    box.name = f'Office {index + 1}'
    boxes.append(box)

main_box: FittedBox = FittedBox(boxes, name='Error')


class MapDemoGame(Game):
    def before_run(self) -> None:
        super().before_run()
        box: Box
        for box in boxes:
            box.context = self.audio_context
        main_box.context = self.audio_context


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
            coordinates.x = x
            coordinates.y = y
            box.dispatch_event('on_footstep')
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
