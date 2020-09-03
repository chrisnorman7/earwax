from pytest import fixture
from synthizer import Context, initialize, shutdown

from earwax import Box, BoxLevel, Editor, Game, Level, Menu, Point


@fixture(name='level')
def get_level() -> Level:
    """Get a new Level instance."""
    return Level()


@fixture(name='game')
def get_game() -> Game:
    return Game()


@fixture(name='menu')
def get_menu(game: Game) -> Menu:
    return Menu('Test Menu', game)


@fixture(name='editor')
def get_editor(game: Game) -> Editor:
    return Editor(print, game)


@fixture(scope='session')
def initialise_tests():
    initialize()
    yield
    shutdown()


@fixture(name='context', scope='session')
def get_context() -> Context:
    return Context()


@fixture(name='box')
def get_box() -> Box:
    return Box(Point(0, 0), Point(5, 5))


@fixture(name='box_level')
def box_level(game: Game, box) -> BoxLevel:
    return BoxLevel(game, box)
