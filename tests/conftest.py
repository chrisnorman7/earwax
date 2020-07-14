from pytest import fixture

from earwax import Editor, Game, Menu


@fixture(name='game')
def get_game():
    return Game('Test')


@fixture(name='menu')
def get_menu():
    return Menu('Test Menu')


@fixture(name='editor')
def get_editor():
    return Editor(text='test')
