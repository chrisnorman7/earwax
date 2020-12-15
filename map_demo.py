"""Map demo."""

from pathlib import Path
from typing import Generator, List

from pyglet.window import Window, key, mouse

from earwax import (Ambiance, Box, BoxLevel, Door, Editor, FittedBox, Game,
                    Point, Portal, box_row)
from earwax.cmd.constants import sounds_directory, surfaces_directory

wall_sounds = sounds_directory / 'walls'

boxes: List[Box] = [
    Box(
        Point(0, 0, 0), Point(99, 2, 2), name='Main Corridor',
        surface_sound=surfaces_directory / 'gridwork'
    ),
    Box(
        Point(0, 3, 0), Point(0, 12, 2), wall=True, wall_sound=wall_sounds,
        name='Western wall'
    ),
    Box(
        Point(0, -1, 0), Point(100, -1, 2), wall=True, wall_sound=wall_sounds,
        name='Southern wall'
    ),
    Box(
        Point(100, 0, 0), Point(100, 2, 2), wall=True, wall_sound=wall_sounds,
        name='Fill up the eastern wall'
    )
]

door_sounds_directory: Path = sounds_directory / 'doors'
index: int
box: Box
for index, box in enumerate(box_row(
    Point(1, 4, 0), Point(19, 9, 2), 5, Point(2, 0, 0))
):
    box.surface_sound = surfaces_directory / 'concrete'
    box.name = f'Office {index + 1}'
    boxes.append(box)
    door_coordinates: Point = box.bottom_left + Point(1, -1, 0)
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
    box_row(
        Point(20, 4, 0), Point(1, 9, 2), 5, Point(20, 0, 0),
        wall=True, wall_sound=wall_sounds
    )
)

boxes.extend(
    box_row(
        Point(1, 3, 0), Point(100, 1, 2), 2, Point(0, 10, 0),
        wall=True, wall_sound=wall_sounds
    )
)

main_portal_point: Point = Point(99, 1, 0)
main_portal_box: Box = Box(
    main_portal_point, main_portal_point, name=boxes[0].name,
    surface_sound=surfaces_directory / 'concrete'
)
boxes.append(main_portal_box)

back_office: Box = Box(
    Point(100, 100, 100), Point(125, 125, 102), name='Back Office'
)
back_portal_box: Box = Box(
    back_office.bottom_left, back_office.bottom_left, name=back_office.name
)

boxes.extend(
    [
        back_office,
        back_portal_box
    ]
)
main_box: FittedBox = FittedBox(boxes, name='Error')

game: Game = Game()
window: Window = Window(caption='Map Demo')
main_level: BoxLevel = BoxLevel(game, main_box)

main_portal_box.portal = Portal(
    main_level, back_office.bottom_left,
    enter_sound=door_sounds_directory / 'open.wav'
)
back_portal_box.portal = Portal(
    main_level, main_portal_point,
    enter_sound=door_sounds_directory / 'close.wav'
)

main_level.ambiances.append(
    Ambiance(
        'file', str(sounds_directory / 'exit.wav'),
        coordinates=Point(41.5, 3, 2)
    )
)

main_level.action(
    'Walk forwards', symbol=key.W, mouse_button=mouse.RIGHT, interval=0.4
)(main_level.move())

main_level.action('Turn left 45 degrees', symbol=key.A)(main_level.turn(-45))
main_level.action('Turn right 45 degrees', symbol=key.D)(main_level.turn(45))
main_level.action('About turn', symbol=key.S)(main_level.turn(180))

main_level.action('Show facing', symbol=key.F)(main_level.show_facing())
main_level.action(
    'Show coordinates', symbol=key.C
)(main_level.show_coordinates())

main_level.action('Activate', symbol=key.RETURN)(main_level.activate())


@main_level.action('Quit', symbol=key.ESCAPE)
def do_quit() -> None:
    """Quit the game."""
    window.dispatch_event('on_close')


@main_level.action('Goto', symbol=key.G)
def goto() -> Generator[None, None, None]:
    """Jump to some coordinates."""
    dest: Point = main_level.coordinates.floor()
    y_editor: Editor = Editor(game, text='%d' % main_level.coordinates.y)

    @y_editor.event('on_submit')
    def y_inner(value: str) -> None:
        """Set the y coordinate, and jump the player."""
        try:
            dest.y = int(value)
            if dest == main_level.coordinates:
                game.output('Coordinates unchanged.')
                return None
            main_level.set_coordinates(dest)
            game.output('Moved.')
        except ValueError:
            game.output('Invalid coordinate.')
        finally:
            game.pop_level()

    x_editor: Editor = Editor(game, text='%d' % main_level.coordinates.x)

    @x_editor.event('on_submit')
    def x_inner(value: str) -> Generator[None, None, None]:
        """Set the x coordinate."""
        try:
            dest.x = int(value)
            yield
            game.replace_level(y_editor)
            game.output('Y coordinate: %d' % main_level.coordinates.y)
        except ValueError:
            game.output('Invalid coordinate.')
            game.pop_level()

    yield
    game.push_level(x_editor)
    game.output('X coordinate: %d' % main_level.coordinates.x)


if __name__ == '__main__':
    game.run(window, initial_level=main_level)
