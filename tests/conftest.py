from concurrent.futures import ThreadPoolExecutor

from _pytest.fixtures import FixtureRequest
from pyglet.window import Window
from pytest import fixture
from synthizer import Context, initialize, shutdown

from earwax import Box, BoxLevel, Editor, Game, GameBoard, Level, Menu, Point


@fixture(name='thread_pool', scope='session')
def get_thread_pool() -> ThreadPoolExecutor:
    return ThreadPoolExecutor()


@fixture(name='level')
def get_level(game: Game) -> Level:
    """Get a new Level instance."""
    return Level(game)


@fixture(name='game')
def get_game(context: Context, thread_pool: ThreadPoolExecutor) -> Game:
    g: Game = Game()
    g.audio_context = context
    g.thread_pool = thread_pool
    return g


@fixture(name='menu')
def get_menu(game: Game) -> Menu:
    return Menu(game, 'Test Menu')


@fixture(name='editor')
def get_editor(game: Game, window: Window) -> Editor:
    e: Editor = Editor(game)

    @e.event
    def on_submit(text: str) -> None:
        if game.window is not None:
            game.window.close()

    return e


@fixture(scope='session', autouse=True)
def initialise_tests():
    initialize()
    yield
    shutdown()


@fixture(name='context', scope='session')
def get_context() -> Context:
    return Context()


@fixture(name='box')
def get_box() -> Box:
    return Box(Point(0, 0, 0), Point(5, 5, 0))


@fixture(name='box_level')
def box_level(game: Game, box) -> BoxLevel:
    return BoxLevel(game, box)


@fixture(name='board')
def get_gameboard(game: Game) -> GameBoard[int]:
    return GameBoard(game, Point(2, 2, 2), lambda p: 0)


@fixture(name='window')
def get_window(request: FixtureRequest) -> Window:
    name: str = f'{request.function.__module__}.{request.function.__name__}'
    w: Window = Window(caption=name)
    yield w
    w.close()
