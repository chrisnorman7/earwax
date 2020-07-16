from pytest import fixture

from earwax import Editor, Game, Menu
from synthizer import Context, initialize, shutdown


@fixture(name='game')
def get_game():
    return Game('Test')


@fixture(name='menu')
def get_menu():
    return Menu('Test Menu')


@fixture(name='editor')
def get_editor():
    return Editor(print, text='test')


@fixture(scope='session')
def initialise_tests():
    initialize()
    yield shutdown()


@fixture(name='context', scope='session')
def get_context():
    return Context()
