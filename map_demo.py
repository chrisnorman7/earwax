"""Map demo."""

from pathlib import Path
from typing import List, Optional

from attr import Factory, attrs
from pyglet.window import Window, key
from synthizer import Context, GlobalFdnReverb

from earwax import (Box, BoxBounds, BoxLevel, BoxTypes, Door, Game, Point,
                    play_and_destroy)

sounds_directory: Path = Path('sounds')
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


@attrs(auto_attribs=True)
class MyBox(Box):
    """A box with a collition event attached."""

    surface_sound: Optional[Path] = None
    wall_sound: Path = Factory(lambda: sounds_directory / 'collide.wav')


class MyBoxLevel(BoxLevel):
    """Override a couple of methods."""

    def collide(self, box: Box, coordinates: Point) -> None:
        """Play the appropriate sound."""
        if self.game.audio_context is not None and box.wall_sound is not None:
            play_and_destroy(
                self.game.audio_context, box.wall_sound,
                position=coordinates.coordinates, reverb=box.reverb
            )
        return super().collide(box, coordinates)

    def on_move(self) -> None:
        """Play a footstep sound."""
        box: Optional[Box] = self.get_current_box()
        if box is not None:
            ctx: Optional[Context] = self.game.audio_context
            if ctx is not None and box.surface_sound is not None:
                play_and_destroy(ctx, box.surface_sound, reverb=box.reverb)
        return super().on_move()


game: Game = Game(name='Map Demo')


@game.event
def before_run() -> None:
    """Create rooms and level."""
    office_reverb: OfficeReverb = OfficeReverb(game.audio_context)

    def finalise_office(office: MyBox):
        """Add walls and a door."""
        door: Door = Door()
        start: Point = office.start + Point(3, 0, 0)
        end: Point = Point(start.x, start.y, office.end.z)
        doors.append(
            MyBox(
                start, end, door=door, name=f'Door to {office.name}',
                surface_sound=office.surface_sound, reverb=office_reverb,
                parent=office
            )
        )
        walls.extend(
            [
                MyBox(
                    office.bounds.bottom_back_right + Point(1, 0, 0),
                    office.end + Point(1, 0, 0),
                    type=BoxTypes.solid
                ), MyBox(
                    office.start, end - Point(1, 0, 0), parent=office,
                    type=BoxTypes.solid
                ), MyBox(
                    start + Point(1, 0, 0), office.bounds.top_back_right,
                    parent=office, type=BoxTypes.solid
                )
            ]
        )

    offices: List[MyBox] = MyBox.create_row(
        Point(0, 4, 0), Point(7, 10, 2), 5, Point(2, 0, 0),
        get_name=lambda i: f'Office {i + 1}', on_create=finalise_office,
        surface_sound=footsteps_directory / 'office', reverb=office_reverb
    )
    corridor_reverb: GlobalFdnReverb = GlobalFdnReverb(game.audio_context)
    corridor_reverb.gain = 0.25
    corridor: MyBox = MyBox(
        offices[0].bounds.bottom_back_left - Point(0, 4, 0),
        offices[-1].bounds.top_back_right - Point(0, 1, 0),
        name='Corridor', surface_sound=footsteps_directory / 'corridor',
        reverb=corridor_reverb
    )
    boxes: List[MyBox] = offices + walls + [corridor]
    box = MyBox.create_fitted(
        boxes, name='Main Box', type=BoxTypes.solid,
        pad_start=Point(-1, -1, -1), pad_end=Point(1, 1, 1)
    )
    level: MyBoxLevel = MyBoxLevel(game, box, coordinates=corridor.start)
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
