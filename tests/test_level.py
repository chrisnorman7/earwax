"""Test level instances."""

from pathlib import Path
from typing import List

from pyglet.clock import schedule_once
from pyglet.window import Window, key
from pytest import raises
from synthizer import Context, DirectSource, Source3D, StreamingGenerator

from earwax import (Action, AlreadyDestroyed, Ambiance, Game, IntroLevel,
                    Level, Point, Sound, SoundManager, Track, TrackTypes)


class OnCoverWorks(Exception):
    """The on_cover event worked."""


class OnRevealWorks(Exception):
    """the on_reveal event worked."""


class RegisterAndBindWorks(Exception):
    """The register_and_bind method worked."""


def test_init(level: Level, game: Game) -> None:
    """Test initialisation."""
    assert isinstance(level, Level)
    assert level.actions == []
    assert level.motions == {}


def test_on_text_motion(game: Game, level: Level, window: Window) -> None:
    """Test that text motions are handled properly."""
    motions: List[int] = []

    @level.event
    def on_text_motion(motion: int) -> None:
        """Add levels."""
        motions.append(motion)
        if motion == key.MOTION_BEGINNING_OF_LINE:
            window.close()

    def push_motions(dt: float) -> None:
        window.dispatch_event("on_text_motion", key.MOTION_BACKSPACE)
        window.dispatch_event("on_text_motion", key.MOTION_BEGINNING_OF_LINE)

    @game.event
    def before_run() -> None:
        schedule_once(push_motions, 0.1)

    game.run(window, initial_level=level)
    assert motions == [key.MOTION_BACKSPACE, key.MOTION_BEGINNING_OF_LINE]


def test_on_push(game: Game, level: Level) -> None:
    """Test the on_push event."""
    push_level: Level = Level(game)

    @level.event
    def on_push() -> None:
        game.push_level(push_level)

    game.push_level(level)
    assert game.levels == [level, push_level]


def test_on_pop(level: Level, game: Game) -> None:
    """Test the on_pop event."""
    pop_level: Level = Level(game)

    @level.event
    def on_pop() -> None:
        game.push_level(pop_level)

    game.push_level(level)
    game.pop_level()
    assert game.levels == [pop_level]


def test_on_reveal(game: Game, level: Level) -> None:
    """Test the on_reveal event."""
    covering_level: Level = Level(game)

    @level.event
    def on_reveal() -> None:
        raise OnRevealWorks()

    game.push_level(level)
    game.push_level(covering_level)
    with raises(OnRevealWorks):
        game.pop_level()


def test_action(game: Game, level: Level) -> None:
    """Test the game.action method."""
    game.push_level(level)
    a = level.action("Print")(print)
    assert isinstance(a, Action)
    assert a.title == "Print"
    assert a.func is print
    assert a.symbol is None
    assert a.modifiers == 0
    assert a.interval is None
    assert a.last_run == 0.0
    assert level.actions == [a]


def test_on_cover(game: Game, level: Level) -> None:
    """Test the on_cover event."""
    l: Level = Level(game)

    @level.event
    def on_cover(lev: Level) -> None:
        assert lev is l
        raise OnCoverWorks()

    game.push_level(level)
    with raises(OnCoverWorks):
        game.push_level(l)
    assert game.level is level
    game.pop_level()
    assert game.level is None
    game.push_level(l)
    assert game.level is l
    game.push_level(level)
    assert game.level is level


def test_start_ambiances(
    context: Context, game: Game, level: Level, window: Window
) -> None:
    """Test that ambiances start correctly."""
    a: Ambiance = Ambiance.from_path(Path("sound.wav"), Point(0, 0, 0))
    level.ambiances.append(a)

    @level.event
    def on_push() -> None:
        """Schedule the real test method."""

        def inner(dt: float) -> None:
            assert isinstance(a.sound, Sound)
            assert a.sound.context is context
            assert a.sound.position == a.coordinates
            assert isinstance(a.sound.source, Source3D)
            assert a.sound.source.position == a.coordinates.coordinates
            assert (
                a.sound.source.gain == game.config.sound.ambiance_volume.value
            )
            assert a.sound.generator.looping is True
            window.close()

        schedule_once(inner, 0.25)

    game.run(window, initial_level=level)


def test_start_tracks(
    context: Context, game: Game, level: Level, window: Window
) -> None:
    """Test that tracks start properly."""
    music: Track = Track.from_path(Path("sound.wav"), TrackTypes.music)
    assert music.protocol == "file"
    assert music.path == "sound.wav"
    ambiance: Track = Track.from_path(Path("move.wav"), TrackTypes.ambiance)
    assert ambiance.protocol == "file"
    assert ambiance.path == "move.wav"
    level.tracks.extend([ambiance, music])

    @level.event
    def on_push() -> None:
        """Schedule the real test function."""

        def inner(dt: float) -> None:
            assert isinstance(ambiance.sound, Sound)
            assert isinstance(ambiance.sound.generator, StreamingGenerator)
            assert ambiance.sound.generator.looping is True
            assert ambiance.sound.position is None
            assert isinstance(ambiance.sound.source, DirectSource)
            assert ambiance.sound.gain == game.config.sound.music_volume.value
            assert isinstance(music.sound, Sound)
            assert isinstance(music.sound.generator, StreamingGenerator)
            assert music.sound.generator.looping is True
            assert music.sound.position is None
            assert isinstance(music.sound.source, DirectSource)
            assert music.sound.gain == game.config.sound.music_volume.value
            window.close()

        schedule_once(inner, 0.25)

    game.run(window, initial_level=level)


def test_register_and_bind(level: Level) -> None:
    """Make sure the register_and_bind method works properly."""

    @level.register_and_bind
    def on_test() -> None:
        raise RegisterAndBindWorks()

    with raises(RegisterAndBindWorks):
        level.dispatch_event("on_test")


def test_intro_level(window: Window, level: Level, game: Game) -> None:
    """Test the IntroLevel class."""
    intro: IntroLevel
    with raises(AssertionError):
        intro = IntroLevel(
            game, level, Path("sound.wav"), skip_after=5.0, looping=True
        )
    intro = IntroLevel(game, level, Path("sound.wav"))
    assert isinstance(intro.sound_manager, SoundManager)
    assert intro.sound_manager is game.interface_sound_manager
    assert intro.sound_path == Path("sound.wav")
    assert intro.sound is None

    @intro.event
    def on_push() -> None:
        def inner(dt: float) -> None:
            assert isinstance(intro.sound_manager, SoundManager)
            assert isinstance(intro.sound, Sound)
            assert intro.sound_manager is game.interface_sound_manager

        schedule_once(inner, 0.5)

    def f(dt: float) -> None:
        window.close()

    schedule_once(f, 2.0)
    game.run(window, initial_level=intro)
    assert game.level is intro
    assert isinstance(intro.sound_manager, SoundManager)
    assert intro.sound_manager is game.interface_sound_manager


def test_intro_level_skip_after(
    window: Window, level: Level, game: Game
) -> None:
    """Test what happens when skip_after is set."""
    intro: IntroLevel = IntroLevel(
        game, level, Path("sound.wav"), skip_after=0.5
    )

    @level.event
    def on_push() -> None:
        def inner(dt: float) -> None:
            window.close()

        schedule_once(inner, 0.2)

    game.run(window, initial_level=intro)
    assert game.level is level
    assert intro.sound_manager is game.interface_sound_manager
    assert intro.sound is None


def test_intro_level_looping(window: Window, level: Level, game: Game) -> None:
    """Test that intro levels loop properly."""
    intro: IntroLevel = IntroLevel(
        game, level, Path("sound.wav"), looping=True
    )

    @level.event
    def on_push() -> None:
        def inner(dt: float) -> None:
            window.close()

        schedule_once(inner, 0.2)

    def f(dt: float) -> None:
        window.close()

    schedule_once(f, 2.0)

    game.run(window, initial_level=intro)
    assert game.level is intro
    assert isinstance(intro.sound_manager, SoundManager)
    assert isinstance(intro.sound, Sound)
    intro.dispatch_event("on_pop")


def test_intro_level_skip(window: Window, level: Level, game: Game) -> None:
    """Test skipping an IntroLevel instance."""
    sounds: List[Sound] = []
    intro: IntroLevel = IntroLevel(
        game, level, Path("sound.wav"), skip_after=5.0
    )

    @level.event
    def on_push() -> None:
        assert intro.sound is None

        def inner(dt: float) -> None:
            window.close()

        schedule_once(inner, 0.2)

    def f(dt: float) -> None:
        assert isinstance(intro.sound, Sound)
        sounds.append(intro.sound)
        list(intro.skip())

    schedule_once(f, 0.5)
    game.run(window, initial_level=intro)
    assert game.level is level
    assert intro.sound_manager is game.interface_sound_manager
    assert intro.sound is None
    with raises(AlreadyDestroyed):
        sounds[0].destroy()
