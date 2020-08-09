"""Test editors."""

from earwax import Game
from pytest import raises
from pyglet.window import key

from earwax import Editor


class Works(Exception):
    pass


def test_init(game: Game, editor: Editor) -> None:
    assert editor.func is print
    assert editor.text == ''
    assert editor.cursor_position is None
    assert editor.dismissible is True


def test_submit(game: Game) -> None:
    def on_submit(text: str) -> None:
        raise Works(text)

    e = Editor(game, on_submit, text='test')
    game.push_level(e)
    with raises(Works) as exc:
        game.on_key_press(key.RETURN, 0)
    assert exc.value.args == (e.text,)


def test_on_text(game: Game, editor: Editor) -> None:
    game.push_level(editor)
    game.on_text('hello')
    assert editor.text == 'hello'
    game.on_text('world')
    assert editor.text == 'helloworld'
    editor.set_cursor_position(5)
    game.on_text(' ')
    assert editor.text == 'hello world'


def test_on_text_motion(game, editor: Editor) -> None:
    editor.text = 'hello world'
    game.push_level(editor)
    game.on_text_motion(key.MOTION_BACKSPACE)
    assert editor.text == 'hello worl'
    game.on_text_motion(key.MOTION_BEGINNING_OF_LINE)
    assert editor.cursor_position == 0
    game.on_text_motion(key.MOTION_DELETE)
    assert editor.text == 'ello worl'
    game.on_text_motion(key.MOTION_END_OF_LINE)
    assert editor.cursor_position is None
