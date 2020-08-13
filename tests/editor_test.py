"""Test editors."""

from pyglet.window import key
from pytest import raises

from earwax import Editor, Game


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

    e = Editor(on_submit, game, text='test')
    game.push_level(e)
    with raises(Works) as exc:
        game.press_key(key.RETURN, 0, string='\n')
    assert exc.value.args == (e.text,)


def test_on_text(game: Game, editor: Editor) -> None:
    game.push_level(editor)
    editor.on_text('hello')
    assert editor.text == 'hello'
    editor.on_text('world')
    assert editor.text == 'helloworld'
    editor.set_cursor_position(5)
    editor.on_text(' ')
    assert editor.text == 'hello world'


def test_on_text_motion(game, editor: Editor) -> None:
    editor.text = 'hello world'
    game.push_level(editor)
    editor.on_text_motion(key.MOTION_BACKSPACE)
    assert editor.text == 'hello worl'
    editor.on_text_motion(key.MOTION_BEGINNING_OF_LINE)
    assert editor.cursor_position == 0
    editor.on_text_motion(key.MOTION_DELETE)
    assert editor.text == 'ello worl'
    editor.on_text_motion(key.MOTION_END_OF_LINE)
    assert editor.cursor_position is None
