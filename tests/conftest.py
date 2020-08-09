from pytest import fixture
from synthizer import Context, initialize, shutdown

from earwax import Editor, Game, Level, Menu


@fixture(name='level')
def get_level(game: Game) -> Level:
    """Get a new Level instance."""
    return Level(game)


@fixture(name='game')
def get_game() -> Game:
    return Game()


@fixture(name='menu')
def get_menu(game: Game) -> Menu:
    return Menu(game, 'Test Menu')


@fixture(name='editor')
def get_editor(game: Game) -> Editor:
    return Editor(game, print)


@fixture(scope='session')
def initialise_tests():
    initialize()
    yield
    shutdown()


@fixture(name='context', scope='session')
def get_context() -> Context:
    return Context()
