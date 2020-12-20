"""Map demo."""

from pathlib import Path
from typing import List, Optional

from pyglet.window import Window, key
from synthizer import GlobalFdnReverb

from earwax import Box, BoxBounds, BoxLevel, BoxTypes, Door, Game, Point

sounds_directory: Path = Path('sounds')
wall_sound: Path = sounds_directory / 'collide.wav'
footsteps_directory: Path = sounds_directory / 'footsteps'

walls: List[Box] = []
doors: List[Box] = []


class OfficeReverb(GlobalFdnReverb):
    """A custom reverb.

    Preset name: Office
    """

    name: str

    def __init__(self, *args, **kwargs) -> None:
        """Initialise reverb."""
        super().__init__(*args, **kwargs)
        self.name = 'Untitled Reverb'
        self.gain = 0.25
        self.input_filter_cutoff = 2000.0
        self.input_filter_enabled = True
        self.late_reflections_delay = 0.009999999776482582
        self.late_reflections_diffusion = 1.0
        self.late_reflections_hf_rolloff = 0.5
        self.late_reflections_lf_reference = 200.0
        self.late_reflections_lf_rolloff = 1.0
        self.late_reflections_modulation_depth = 0.009999999776482582
        self.late_reflections_modulation_frequency = 0.5
        self.mean_free_path = 0.019999999552965164
        self.t60 = 0.699999988079071


game: Game = Game(name='Map Demo')


@game.event
def before_run() -> None:
    """Create rooms and level."""
    office_reverb: OfficeReverb = OfficeReverb(game.audio_context)

    def finalise_office(office: Box):
        """Add walls and a door."""
        door: Door = Door()
        start: Point = office.start + Point(3, 0, 0)
        end: Point = Point(start.x, start.y, office.end.z)
        doors.append(
            Box(
                start, end, door=door, name=f'Door to {office.name}',
                surface_sound=office.surface_sound, reverb=office_reverb,
                parent=office, wall_sound=wall_sound
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
        surface_sound=footsteps_directory / 'office', reverb=office_reverb,
        wall_sound=wall_sound
    )
    corridor_reverb: GlobalFdnReverb = GlobalFdnReverb(game.audio_context)
    corridor_reverb.gain = 0.25
    corridor: Box = Box(
        offices[0].bounds.bottom_back_left - Point(0, 4, 0),
        offices[-1].bounds.top_back_right - Point(0, 1, 0),
        name='Corridor', surface_sound=footsteps_directory / 'corridor',
        reverb=corridor_reverb, wall_sound=wall_sound
    )
    boxes: List[Box] = offices + walls + [corridor]
    box = Box.create_fitted(
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