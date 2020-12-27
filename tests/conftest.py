"""Setup for tests."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from socket import AF_INET, SOCK_STREAM
from typing import Generator

from _pytest.fixtures import FixtureRequest
from pyglet.window import Window
from pytest import fixture
from synthizer import (Context, GlobalFdnReverb, Source3D, StreamingGenerator,
                       initialized)

from earwax import (
    Box, BoxLevel, DialogueTree, Door, Editor, Game, GameBoard, Level, Menu,
    NetworkConnection, Point, Sound, SoundManager, Track, TrackTypes)

from .networking.pretend_socket import PretendSocket


@fixture(name='thread_pool', scope='session')
def get_thread_pool() -> ThreadPoolExecutor:
    """Get a new thread pool executor."""
    return ThreadPoolExecutor()


@fixture(name='level')
def get_level(game: Game) -> Level:
    """Get a new Level instance."""
    return Level(game)


@fixture(name='game')
def get_game(context: Context, thread_pool: ThreadPoolExecutor) -> Game:
    """Get a new ``Game`` instance."""
    g: Game = Game(audio_context=context, thread_pool=thread_pool)
    return g


@fixture(name='menu')
def get_menu(game: Game) -> Menu:
    """Return an empty ``Menu`` instance."""
    return Menu(game, 'Test Menu')


@fixture(name='editor')
def get_editor(game: Game, window: Window) -> Editor:
    """Return a new ``Editor`` instance.

    The default submit event handler closes the window.
    """
    e: Editor = Editor(game)

    @e.event
    def on_submit(text: str) -> None:
        if game.window is not None:
            game.window.close()

    return e


@fixture(scope='session', autouse=True)
def initialise_tests() -> Generator[None, None, None]:
    """Initialise and shutdown Synthizer."""
    with initialized():
        yield


@fixture(name='context', scope='session')
def get_context() -> Context:
    """Get a new Synthizer context."""
    return Context()


@fixture(name='box')
def get_box(game: Game) -> Box:
    """Get a new ``Box`` instance."""
    return Box(game, Point(1, 2, 3), Point(4, 5, 6))


@fixture(name='box_level')
def get_box_level(game: Game) -> BoxLevel:
    """Get a new ``BoxLevel`` instance."""
    box: Box = Box(game, Point(1, 1, 1), Point(5, 5, 5))
    return BoxLevel(game, box)


@fixture(name='board')
def get_gameboard(game: Game) -> GameBoard[int]:
    """Get a new ``GameBoard`` instance."""
    return GameBoard(game, Point(2, 2, 2), lambda p: 0)


@fixture(name='window')
def get_window(request: FixtureRequest) -> Window:
    """Get a pyglet window with a sensible caption."""
    name: str = f'{request.function.__module__}.{request.function.__name__}'
    w: Window = Window(caption=name)
    yield w
    w.close()


@fixture(name='con')
def get_network_connection() -> NetworkConnection:
    """Get a new network connection."""
    return NetworkConnection()


@fixture(name='socket')
def get_socket() -> PretendSocket:
    """Get a pretend socket."""
    return PretendSocket(AF_INET, SOCK_STREAM)


@fixture(name='generator')
def get_streaming_generator(context: Context) -> StreamingGenerator:
    """Return a new ``StreamingGenerator`` instance."""
    return StreamingGenerator(context, 'file', 'sound.wav')


@fixture(name='source')
def get_source_3d(context: Context) -> Source3D:
    """Get a new ``Source3D`` instance."""
    return Source3D(context)


@fixture(name='sound_manager')
def get_sound_manager(context: Context, source: Source3D) -> SoundManager:
    """Get a new sound manager instance."""
    return SoundManager(context, source)


@fixture(name='sound')
def get_sound(context: Context, source: Source3D) -> Sound:
    """Get a new sound."""
    return Sound.from_path(context, source, Path('sound.wav'))


@fixture(name='track')
def get_track() -> Track:
    """Get a new track instance."""
    return Track('file', 'sound.wav', TrackTypes.ambiance)


@fixture(name='reverb')
def get_reverb(context: Context) -> GlobalFdnReverb:
    """Get a new reverb object."""
    return GlobalFdnReverb(context)


@fixture(name='door')
def get_door() -> Door:
    """Get a door object."""
    p: Path = Path('sound.wav')
    return Door(open_sound=p, close_sound=p, closed_sound=p)


@fixture(name='dialogue_tree')
def get_dialogue_line() -> DialogueTree:
    """Get a new DialogueTree instance."""
    return DialogueTree()
