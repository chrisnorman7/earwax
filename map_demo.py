"""Map demo."""

from pathlib import Path
from typing import List, Optional

from pyglet.window import Window, key

from earwax import (Box, BoxBounds, BoxLevel, BoxTypes, Door, Game, Point,
                    play_and_destroy)

sounds_directory: Path = Path('sounds')
footsteps_directory: Path = sounds_directory / 'footsteps'

walls: List[Box] = []
doors: List[Box] = []


class MyBox(Box):
    """A box with a collition event attached."""

    def on_collide(self, coordinates: Point) -> None:
        """Play the right sound."""
        play_and_destroy(
            game.audio_context, sounds_directory / 'collide.wav',
            position=coordinates.coordinates
        )
        return super().on_collide(coordinates)


def finalise_office(office: MyBox):
    """Add a wall and a door."""
    door: Door = Door()
    start: Point = office.start + Point(3, -1, 0)
    end: Point = Point(start.x, start.y, office.end.z)
    doors.append(
        MyBox(
            start, end, door=door, name=f'Door to {office.name}',
            surface_sound=office.surface_sound
        )
    )
    walls.append(
        MyBox(
            office.bounds.bottom_back_right + Point(1, 0, 0),
            office.end + Point(1, 0, 0),
            type=BoxTypes.solid
        )
    )


offices: List[MyBox] = MyBox.create_row(
    Point(0, 4, 0), Point(7, 10, 2), 5, Point(2, 0, 0),
    get_name=lambda i: f'Office {i + 1}',
    surface_sound=footsteps_directory / 'office', on_create=finalise_office
)

corridor: MyBox = MyBox(
    offices[0].bounds.bottom_back_left - Point(0, 4, 0),
    offices[-1].bounds.top_back_right - Point(0, 1, 0),
    name='Corridor', surface_sound=footsteps_directory / 'corridor'
)
wall: MyBox = MyBox(
    corridor.bounds.bottom_front_left, corridor.end, type=BoxTypes.solid,
    parent=corridor
)

boxes: List[MyBox] = offices + walls + doors + [corridor]

game: Game = Game(name='Map Demo')

box = MyBox.create_fitted(
    boxes, name='Main Box', type=BoxTypes.solid,
    pad_start=Point(-1, -1, -1), pad_end=Point(1, 1, 1)
)

level: BoxLevel = BoxLevel(game, box, coordinates=corridor.start)

level.action('Show coordinates', symbol=key.C)(level.show_coordinates())
level.action('Show facing direction', symbol=key.F)(level.show_facing())
level.action('Walk forwards', symbol=key.W, interval=0.5)(level.move())
level.action(
    'Walk backwards', symbol=key.S, interval=1.0
)(level.move(distance=-0.5))
level.action('Turn right', symbol=key.D)(level.turn(45))
level.action('Turn left', symbol=key.A)(level.turn(-45))
level.action('Activate nearby objects', symbol=key.RETURN)(level.activate())


@level.action('Describe current box', symbol=key.X)
def describe_current_box() -> None:
    """Describe the current box."""
    box: Optional[Box] = level.box.get_containing_box(
        level.coordinates.floor()
    )
    if box is None:
        game.output('No box.')
    else:
        b: BoxBounds = box.bounds
        game.output(
            f'{box.name}: {b.width + 1} x {b.depth + 1} x {b.height + 1}.'
        )


if __name__ == '__main__':
    window: Window = Window(caption='Map Demo')
    game.run(window, initial_level=level)
