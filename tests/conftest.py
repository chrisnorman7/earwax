from pytest import fixture
from synthizer import Context, initialize, shutdown

from earwax import Editor, Game, Level, Menu  # noqa: E402


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
