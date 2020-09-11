from pytest import fixture
from synthizer import Context, initialize, shutdown

from earwax import Box, BoxLevel, Editor, Game, Level, Menu, Point, GameBoard


@fixture(name='level')
def get_level(game: Game) -> Level:
    """Get a new Level instance."""
    return Level(game)


@fixture(name='game')
def get_game(context: Context) -> Game:
    g: Game = Game()
    g.audio_context = context
    return g


@fixture(name='menu')
def get_menu(game: Game) -> Menu:
    return Menu(game, 'Test Menu')


@fixture(name='editor')
def get_editor(game: Game) -> Editor:
    return Editor(game, print)


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
