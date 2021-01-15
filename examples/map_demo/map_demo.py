"""Map demo."""

if True:
    import sys
    sys.path.insert(0, '../..')

from pathlib import Path
from typing import List

from pyglet.window import Window, key
from synthizer import GlobalFdnReverb

from earwax import (ActionMenu, Ambiance, Box, BoxLevel, BoxTypes, Credit,
                    Door, Game, Level, Menu, Point, Reverb, Track, TrackTypes)

sounds_directory: Path = Path('sounds')
wall_sound: Path = sounds_directory / 'collide.wav'
footsteps_directory: Path = sounds_directory / 'footsteps'
doors_directory: Path = sounds_directory / 'doors'

walls: List[Box] = []
doors: List[Box] = []

office_reverb: Reverb = Reverb(gain=00.25, t60=0.9)

corridor_reverb: Reverb = Reverb(gain=0.25, t60=1.0)

game: Game = Game(
    name='Map Demo', credits=[
        Credit(
            'Camlorn, for producing the amazing Synthizer audio library',
            'https://github.com/synthizer',
            sound=sounds_directory / 'keyboard.wav'
        ), Credit(
            'The folks over at freesound.org for making awesome free sounds',
            'https://www.freesound.org', sound=sounds_directory / 'ukulele.wav'
        )
    ]
)


@game.event
def before_run() -> None:
    """Create rooms and level."""
    boxes: List[Box] = []
    ambiances: List[Ambiance] = []

    def finalise_office(office: Box):
        """Add walls and a door."""
        door: Door = Door(
            open_sound=doors_directory / 'open.wav',
            close_sound=doors_directory / 'close.wav',
            closed_sound=doors_directory / 'closed.wav',
            open=False, close_after=(2.0, 5.0)
        )
        start: Point = office.start + Point(3, 0, 0)
        end: Point = Point(start.x + 1, start.y, office.end.z)
        b: Box[Door] = Box(
            game, start, end, data=door, name=f'Door to {office.name}',
            surface_sound=office.surface_sound, reverb=office_reverb.make_reverb(game.audio_context)
        )
        boxes.append(b)
        a: Ambiance = Ambiance.from_path(
            sounds_directory / ('buzz_%d.wav' % len(ambiances)),
            coordinates=b.centre
        )
        ambiances.append(a)
        boxes.extend(
            [
                Box(
                    game, office.bounds.bottom_back_right + Point(1, 0, 0),
                    office.end + Point(1, 0, 0),
                    type=BoxTypes.solid, wall_sound=wall_sound
                ), Box(
                    game, office.start.copy(), start - Point(1, 0, 0),
                    type=BoxTypes.solid, wall_sound=wall_sound
                ), Box(
                    game, start + Point(2, 0, 0),
                    office.bounds.top_back_right.copy(),
                    type=BoxTypes.solid, wall_sound=wall_sound
                )
            ]
        )

    offices: List[Box] = Box.create_row(
        game, Point(0, 4, 0), Point(7, 10, 2), 3, Point(2, 0, 0),
        get_name=lambda i: f'Office {i + 1}', on_create=finalise_office,
        surface_sound=footsteps_directory / 'office',
        reverb=office_reverb.make_reverb(game.audio_context), wall_sound=wall_sound
    )
    boxes.append(
        Box(
            game, offices[0].bounds.bottom_back_left - Point(0, 4, 0),
            offices[-1].bounds.top_back_right - Point(0, 1, 0),
            name='Corridor', surface_sound=footsteps_directory / 'corridor',
            reverb=corridor_reverb.make_reverb(game.audio_context), wall_sound=wall_sound
        )
    )
    boxes.extend(offices)
    boxes.append(
        Box.create_fitted(
            game, boxes, name='Main Box', type=BoxTypes.solid,
            pad_start=Point(-1, -1, -1), pad_end=Point(1, 1, 1),
            wall_sound=wall_sound
        )
    )
    music: Track = Track.from_path(
        sounds_directory / 'music.mp3', TrackTypes.music
    )
    level: BoxLevel = BoxLevel(game, boxes=boxes)
    level.tracks.append(music)
    level.ambiances.extend(ambiances)
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

    level.action(
        'Announce nearest door', symbol=key.Z
    )(level.show_nearest_door())
    level.action(
        'Describe current box', symbol=key.X
    )(level.describe_current_box)

    @level.action('Help menu', symbol=key.SLASH, modifiers=key.MOD_SHIFT)
    def help_menu() -> None:
        """Show the help menu."""
        m: ActionMenu = game.push_action_menu()

        @m.event
        def on_cover(new: Level) -> None:
            """Stop the tracks playing."""
            level.stop_ambiances()
            level.stop_tracks()

        @m.event
        def on_reveal() -> None:
            """Start the tracks again."""
            level.start_ambiances()
            level.start_tracks()

        credits_menu: Menu = Menu.from_credits(game, game.credits)
        credits_menu.tracks.append(
            Track.from_path(sounds_directory / 'drums.wav', TrackTypes.music)
        )
        m.add_submenu(credits_menu, False, title='Credits')

    game.push_level(level)


if __name__ == '__main__':
    window: Window = Window(caption='Map Demo')
    game.run(window)
