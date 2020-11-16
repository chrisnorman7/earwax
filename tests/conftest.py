"""Setup for tests."""

from concurrent.futures import ThreadPoolExecutor
from typing import Generator

from _pytest.fixtures import FixtureRequest
from earwax import (Box, BoxLevel, Editor, Game, GameBoard, Level, Menu,
                    NetworkConnection, Point)
from pyglet.window import Window
from pytest import fixture
from synthizer import Context, initialize, shutdown


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
    g: Game = Game()
    g.audio_context = context
    g.thread_pool = thread_pool
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
    initialize()
    yield
    shutdown()


@fixture(name='context', scope='session')
def get_context() -> Context:
    """Get a new Synthizer context."""
    return Context()


@fixture(name='box')
def get_box() -> Box:
    """Get a new ``Box`` instance."""
    return Box(Point(0, 0, 0), Point(5, 5, 0))


@fixture(name='box_level')
def box_level(game: Game, box) -> BoxLevel:
    """Get a new ``BoxLevel`` instance."""
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
