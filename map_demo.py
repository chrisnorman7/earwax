from pathlib import Path
from typing import Generator, List

from pyglet.window import Window, key, mouse

from earwax import (Ambiance, Box, BoxLevel, Door, Editor, FittedBox, Game,
                    Point, box_row, tts)
from earwax.cmd.constants import sounds_directory, surfaces_directory

wall_sounds = sounds_directory / 'walls'

boxes: List[Box] = [
    Box(
        Point(0, 0), Point(99, 2), name='Main Corridor',
        surface_sound=surfaces_directory / 'gridwork'
    ),
    Box(
        Point(0, 3), Point(0, 12), wall=True, wall_sound=wall_sounds,
        name='Western wall'
    ),
    Box(
        Point(0, -1), Point(100, -1), wall=True, wall_sound=wall_sounds,
        name='Southern wall'
    ),
    Box(
        Point(100, 0), Point(100, 2), wall=True, wall_sound=wall_sounds,
        name='Fill up the eastern wall'
    )
]

door_sounds_directory: Path = sounds_directory / 'doors'
index: int
box: Box
for index, box in enumerate(box_row(Point(1, 4), 19, 9, 5, 2, 0)):
    box.surface_sound = surfaces_directory / 'concrete'
    box.name = f'Office {index + 1}'
    boxes.append(box)
    door_coordinates: Point = box.bottom_left + Point(1, -1)
    door: Box = Box(
        door_coordinates, door_coordinates, name='Office Entrance',
        surface_sound=surfaces_directory / 'concrete', door=Door(
            open=False, closed_sound=door_sounds_directory / 'closed.wav',
            open_sound=door_sounds_directory / 'open.wav',
            close_sound=door_sounds_directory / 'close.wav', close_after=(
                3.0, 5.0
            )
        )
    )
    boxes.append(door)

boxes.extend(
    box_row(Point(20, 4), 1, 9, 5, 20, 0, wall=True, wall_sound=wall_sounds)
)

boxes.extend(
    box_row(Point(1, 3), 100, 1, 2, 0, 10, wall=True, wall_sound=wall_sounds)
)

main_box: FittedBox = FittedBox(boxes, name='Error')

game: Game = Game()
window: Window = Window(caption='Map Demo')
level: BoxLevel = BoxLevel(game, main_box)

level.ambiances.append(Ambiance(41.5, 3, sounds_directory / 'exit.wav'))

level.action(
    'Walk forwards', symbol=key.W, mouse_button=mouse.RIGHT, interval=0.4
)(level.move())

level.action('Turn left 45 degrees', symbol=key.A)(level.turn(-45))
level.action('Turn right 45 degrees', symbol=key.D)(level.turn(45))
level.action('About turn', symbol=key.S)(level.turn(180))

level.action('Show facing', symbol=key.F)(level.show_facing())
level.action('Show coordinates', symbol=key.C)(level.show_coordinates)

level.action('Activate', symbol=key.RETURN)(level.activate())


@level.action('Quit', symbol=key.ESCAPE)
def do_quit() -> None:
    """Quit the game."""
    window.dispatch_event('on_close')


@level.action('Goto', symbol=key.G)
def goto() -> Generator[None, None, None]:
    """Jump to some coordinates."""
    dest: Point = Point(int(level.x), int(level.y))

    def y_inner(value: str) -> None:
        """Set the y coordinate, and jump the player."""
        try:
            dest.y = int(value)
            if dest.x == int(level.x) and dest.y == int(level.y):
                tts.speak('Coordinates unchanged.')
                return None
            level.set_coordinates(dest.x, dest.y)
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
            game.replace_level(Editor(game, y_inner, text='%d' % level.y))
            tts.speak('Y coordinate: %d' % level.y)
        except ValueError:
            tts.speak('Invalid coordinate.')
            game.pop_level()

    yield
    game.push_level(Editor(game, x_inner, text='%d' % level.x))
    tts.speak('X coordinate: %d' % level.x)


def main() -> None:
    game.run(window, initial_level=level)


if __name__ == '__main__':
    main()
