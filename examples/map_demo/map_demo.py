"""Map demo."""

if True:
    import sys
    sys.path.insert(0, '../..')

from pathlib import Path
from typing import List, Optional

from pyglet.window import Window, key
from synthizer import DirectSource, GlobalFdnReverb, Source3D

from earwax import (Box, BoxBounds, BoxLevel, BoxTypes, Door, Game, Point,
                    ReverbSettingsDict, SoundManager)

sounds_directory: Path = Path('sounds')
wall_sound: Path = sounds_directory / 'collide.wav'
footsteps_directory: Path = sounds_directory / 'footsteps'
doors_directory: Path = sounds_directory / 'doors'

walls: List[Box] = []
doors: List[Box] = []

office_reverb: ReverbSettingsDict = {
    'gain': 0.25,
    't60': 0.9
}

corridor_reverb: ReverbSettingsDict = {
    'gain': 0.25,
    't60': 1.0
}

game: Game = Game(name='Map Demo')


@game.event
def before_run() -> None:
    """Create rooms and level."""
    player_sound_manager: SoundManager = SoundManager(
        game.audio_context, DirectSource(game.audio_context)
    )
    external_sound_manager: SoundManager = SoundManager(
        game.audio_context, Source3D(game.audio_context)
    )

    def finalise_office(office: Box):
        """Add walls and a door."""
        door: Door = Door(
            open_sound=doors_directory / 'open.wav',
            close_sound=doors_directory / 'close.wav',
            closed_sound=doors_directory / 'closed.wav',
            open=False
        )
        start: Point = office.start + Point(3, 0, 0)
        end: Point = Point(start.x, start.y, office.end.z)
        doors.append(
            Box(
                start, end, door=door, name=f'Door to {office.name}',
                surface_sound=office.surface_sound,
                reverb_settings=office_reverb, parent=office,
                wall_sound=wall_sound
            )
        )
        walls.extend(
            [
                Box(
                    office.bounds.bottom_back_right + Point(1, 0, 0),
                    office.end + Point(1, 0, 0),
                    type=BoxTypes.solid, wall_sound=wall_sound
                ), Box(
                    office.start, end - Point(1, 0, 0), parent=office,
                    type=BoxTypes.solid, wall_sound=wall_sound
                ), Box(
                    start + Point(1, 0, 0), office.bounds.top_back_right,
                    parent=office, type=BoxTypes.solid, wall_sound=wall_sound
                )
            ]
        )

    offices: List[Box] = Box.create_row(
        Point(0, 4, 0), Point(7, 10, 2), 5, Point(2, 0, 0),
        get_name=lambda i: f'Office {i + 1}', on_create=finalise_office,
        surface_sound=footsteps_directory / 'office',
        reverb_settings=office_reverb, wall_sound=wall_sound
    )
    corridor: Box = Box(
        offices[0].bounds.bottom_back_left - Point(0, 4, 0),
        offices[-1].bounds.top_back_right - Point(0, 1, 0),
        name='Corridor', surface_sound=footsteps_directory / 'corridor',
        reverb_settings=corridor_reverb, wall_sound=wall_sound
    )
    boxes: List[Box] = offices + walls + [corridor]
    box = Box.create_fitted(
        boxes, name='Main Box', type=BoxTypes.solid,
        pad_start=Point(-1, -1, -1), pad_end=Point(1, 1, 1),
        wall_sound=wall_sound
    )
    reverb: GlobalFdnReverb = GlobalFdnReverb(game.audio_context)
    level: BoxLevel = BoxLevel(
        game, box, coordinates=corridor.start,
        player_sound_manager=player_sound_manager,
        external_sound_manager=external_sound_manager
    )
    level.connect_reverb(reverb)
    level.action('Show coordinates', symbol=key.C)(level.show_coordinates())
    level.action('Show facing direction', symbol=key.F)(level.show_facing())
    level.action('Walk forwards', symbol=key.W, interval=0.5)(level.move())
    level.action(
        'Walk backwards', symbol=key.S, interval=1.0
    )(level.move(distance=-0.5))
    level.action('Turn right', symbol=key.D)(level.turn(45))
    level.action('Turn left', symbol=key.A)(level.turn(-45))
    level.action(
        'Activate nearby objects', symbol=key.RETURN
    )(level.activate())

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

    game.push_level(level)


if __name__ == '__main__':
    window: Window = Window(caption='Map Demo')
    game.run(window)
